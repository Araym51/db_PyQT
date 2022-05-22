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
from descriptors import Port
from metaclasses import ServerMarker

SERVER_LOGGER = logging.getLogger('server')

@log
def args_reader():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=SERVER_PORT, type=int, nargs='?')
    parser.add_argument('-a', default=SERVER_IP, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    serv_adress = namespace.a
    serv_port = namespace.p

    if not 1023 < serv_port < 65536:
        SERVER_LOGGER.critical(f'Попытка запуска сервера с указанием неподходящего порта '
                               f'{serv_port}. Допустимы адреса с 1024 до 65535.')
        sys.exit(1)

    return serv_adress, serv_port

class Server(metaclass=ServerMarker):
    port = Port()

    def __init__(self, listen_adress, listen_port):
        self.adress = listen_adress
        self.port = listen_port
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
            #72 строка
            else:
                SERVER_LOGGER.info(f'Установлено соедение с ПК {client_address}')
                clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            # Проверяем на наличие ждущих клиентов
            try:
                if clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(clients, clients, [], 0)
            except OSError:
                pass

            # принимаем сообщения и если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        process_client_message(recieve_message(client_with_message),
                                               messages, client_with_message, clients, names)
                    except Exception:
                        SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                           f'отключился от сервера.')
                        clients.remove(client_with_message)

            # Если есть сообщения, обрабатываем каждое.
            for i in messages:
                try:
                    process_message(i, names, send_data_lst)
                except Exception:
                    SERVER_LOGGER.info(f'Связь с клиентом с именем {i[DESTINATION]} была потеряна')
                    clients.remove(names[i[DESTINATION]])
                    del names[i[DESTINATION]]
            messages.clear()


@log
def process_client_message(message, messages_list, client, clients, names):
    """
    функция для проверки корректности входящих данных от клиентов
    :param message:
    :return:
    """
    SERVER_LOGGER.debug(f'Разбор сообщение от клиента: {message}')
    # если клиент сообщает о присутствии, подтверждаем, что видим его
    if ACTION in message and message[ACTION] == PRESENCE and \
            TIME in message and USER in message:
        if message[USER][ACCOUNT_NAME] not in names.keys():
            names[message[USER][ACCOUNT_NAME]] = client
            send_message(client, RESPONSE_200)
        else:
            response = RESPONSE_400
            response[ERROR] = 'Такой пользователь уже в системе'
            send_message(client, response)
            clients.remove(client)
            client.close
        return
    # Если это сообщение, добавляем его в список сообщений
    elif ACTION in message and message[
        ACTION] == MESSAGE and DESTINATION in message and TIME in message and SENDER in message and MESSAGE_TEXT in message:
        messages_list.append(message)
        return
    # клиент выходит
    elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
        clients.remove(names[message[ACCOUNT_NAME]])
        names[message[ACCOUNT_NAME]].close()
        del names[message[ACCOUNT_NAME]]
        return
    else:
        response = RESPONSE_400
        response[ERROR] = 'Некорректый запрос'
        send_message(client, response)
        return


@log
def process_message(message, names, listen_socks):
    """
    функция адресной отправки сообщений
    :param message: словарь сообщения
    :param names: пользователь
    :param listen_socks: слушающие сокеты
    :return:
    """
    if message[DESTINATION] in names and names[message[DESTINATION]] in listen_socks:
        send_message(names[message[DESTINATION]], message)
        SERVER_LOGGER.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                    f'от пользователя {message[SENDER]}.')
    elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_socks:
        raise ConnectionError
    else:
        SERVER_LOGGER.error(f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере'
                            f'отправка сообщения невозможна')


def main():
    #


    # список клиентов , очередь сообщений
    clients = []
    messages = []

    # Словарь, содержащий имена пользователей и соответствующие им сокеты.
    names = dict()

    # Слушаем порт
    transport.listen(MAX_CONNECTIONS)
    # Основной цикл программы сервера



if __name__ == '__main__':
    main()
