import argparse
import socket
import sys
import json
import select
import time
from common.constants import *
from common.utils import send_message, recieve_message
import logging
import loging.server_conf_log
from errors import IncorrectDataRecievedError
from logging_deco import log
from descriptors import Port, Host
from metaclasses import ServerMarker
from server_database import ServerStorage

SERVER_LOGGER = logging.getLogger('server')

@log
def args_reader():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=SERVER_PORT, type=int, nargs='?')
    parser.add_argument('-a', default=SERVER_IP, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    serv_adress = namespace.a
    serv_port = namespace.p
    return serv_adress, serv_port

class Server(metaclass=ServerMarker):
    # контролируем порт и адрес с помощью дескрипторов:
    port = Port()
    adress = Host()

    def __init__(self, listen_adress, listen_port, database):
        self.adress = listen_adress
        self.port = listen_port

        # databse
        self.database = database
        # список клиентов:
        self.clients = []
        # список сообщений на отправку
        self.messages = []

        # словарь с сопоставленными именами и их сокетами
        self.names = dict()

    def init_socket(self):
        listen_address, listen_port = args_reader()

        SERVER_LOGGER.info(
            f'Запущен сервер, порт для подключений: {self.port}, '
            f'адрес с которого принимаются подключения: {self.adress}. '
            f'Если адрес не указан, принимаются соединения с любых адресов.')
        # Готовим сокет
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.adress, self.port))
        transport.settimeout(0.5)
        # слушаем сокет
        self.sock = transport
        self.sock.listen()

    def main_loop(self):
        #инициализируем сокет
        self.init_socket()

        while True:
            # Ждём подключения, если таймаут вышел, ловим исключение.
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                SERVER_LOGGER.info(f'Установлено соедение с ПК {client_address}')
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            # Проверяем на наличие ждущих клиентов
            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            # принимаем сообщения и если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(recieve_message(client_with_message), client_with_message)
                    except:
                        SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        self.clients.remove(client_with_message)

            # Если есть сообщения, обрабатываем каждое.
            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except Exception:
                    SERVER_LOGGER.info(f'Связь с клиентом с именем {message[DESTINATION]} была потеряна')
                    self.clients.remove(self.names[message[DESTINATION]])
                    del self.names[message[DESTINATION]]
            self.messages.clear()

    def process_message(self, message, listen_socks):
        """
        функция адресной отправки сообщений
        :param message: словарь сообщения
        :param names: пользователь
        :param listen_socks: слушающие сокеты
        :return:
        """
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_socks:
            send_message(self.names[message[DESTINATION]], message)
            SERVER_LOGGER.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                               f'от пользователя {message[SENDER]}.')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            SERVER_LOGGER.error(f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере'
                                f'отправка сообщения невозможна')


    def process_client_message(self, message,client,):
        """
        функция для проверки корректности входящих данных от клиентов
        :param message:
        :return:
        """
        SERVER_LOGGER.debug(f'Разбор сообщение от клиента: {message}')
        # если клиент сообщает о присутствии, подтверждаем, что видим его
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Такой пользователь уже в системе.'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        # Если это сообщение, добавляем его в список сообщений
        elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message:
            self.messages.append(message)
            return
        # клиент выходит
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.database.user_logout(message[ACCOUNT_NAME])
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            return
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            send_message(client, response)
            return


def print_help():
    print('Поддерживаемые комманды:')
    print('users - список известных пользователей')
    print('connected - список подключенных пользователей')
    print('loghist - история входов пользователя')
    print('exit - завершение работы сервера.')
    print('help - вывод справки по поддерживаемым командам')


def main():
    listen_adress, listen_port = args_reader()
    database = ServerStorage()
    server = Server(listen_adress, listen_port, database)
    server.main_loop()

    print_help()

    while True:
        command = input('Введите команду: ')
        if command == 'help':
            print_help()
        elif command == 'exit':
            break
        elif command == 'users':
            for user in sorted(database.users_list()):
                print(f'Пользователь {user[0]}, последний вход: {user[1]}\n')
        elif command == 'connected':
            for user in sorted(database.users_list()):
                print(f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, завшел в {user[3]}\n')
        elif command == 'loghist':
            for user in sorted(database.users_list()):
                print(f'Пользователь {user[0]}, время входа: {user[1]}. Вход с: {user[2]}: {user[3]}\n')
        else:
            print("Команда не распознана.")

if __name__ == '__main__':
    main()
