import argparse
import os.path
import socket
import sys
import json
import select
import threading
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
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, gui_create_model, HistoryMainWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import configparser
import os


SERVER_LOGGER = logging.getLogger('server')

new_connection =False
conflag_lock = threading.Lock()

@log
def args_reader(default_port, default_address):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    serv_adress = namespace.a
    serv_port = namespace.p
    return serv_adress, serv_port

class Server(threading.Thread, metaclass=ServerMarker):
    # контролируем порт и адрес с помощью дескрипторов:
    port = Port()

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

        # конструктор родителя
        super().__init__()

    def init_socket(self):
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


    def run(self):
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
            except OSError as error:
                SERVER_LOGGER.error(f'ошибка рабыоты с сокетами {error}')

            # принимаем сообщения и если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(recieve_message(client_with_message), client_with_message)
                    except (OSError):
                        SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_message)

            # Если есть сообщения, обрабатываем каждое.
            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except (ConnectionAbortedError, ConnectionError, ConnectionResetError, ConnectionRefusedError):
                    SERVER_LOGGER.info(f'Связь с клиентом с именем {message[DESTINATION]} была потеряна')
                    self.clients.remove(self.names[message[DESTINATION]])
                    self.database.user_logout(message[DESTINATION])
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
        global new_connection
        SERVER_LOGGER.debug(f'Разбор сообщение от клиента: {message}')
        # если клиент сообщает о присутствии, подтверждаем, что видим его
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, RESPONSE_200)
                with conflag_lock:
                    new_connection = True
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
            self.database.process_message(message[SENDER], message[DESTINATION])
            return
        # клиент выходит
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.database.user_logout(message[ACCOUNT_NAME])
            SERVER_LOGGER.info(f'клиент {message[ACCOUNT_NAME]} корректно отключился от сервера')
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            with conflag_lock:
                new_connection = True
            return

        # запрос списка контактов
        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            send_message(client, RESPONSE_200)

        # удаление контакта
        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200) # добавление нового

        # запрос известных пользователей
        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.database.users_list()]
            send_message(client, response)

        # иначе отдаем bad request
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            send_message(client, response)
            return


# def print_help():
#     print('Поддерживаемые комманды:')
#     print('users - список известных пользователей')
#     print('connected - список подключенных пользователей')
#     print('loghist - история входов пользователя')
#     print('exit - завершение работы сервера.')
#     print('help - вывод справки по поддерживаемым командам')


def main():
    config = configparser.ConfigParser()
    config_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f'{config_path}/{"server.ini"}')

    listen_address, listen_port = args_reader(config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])
    database = ServerStorage(os.path.join(config['SETTINGS']['Database_path'],config['SETTINGS']['Database_file']))
    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    # запуск графического окружения сервера
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('сервер запущен')
    main_window.active_clients_table.setModel(gui_create_model(database)) # заполняем таблицу основного окна
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    # функция обновляет список подключенных пользователей, если нужно обновляет список
    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    # статистика клиента
    def show_statistics():
        global stat_window
        stat_window = HistoryMainWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()

    # окно с настройками сервера
    def server_config():
        global config_window
        config_window = ConfigWindow()
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка!', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки сохранены!')
            else:
                message.warning(config_window, 'Ошибка!', 'Порт должен быть от 1024 до 65536')
    # обновление клиентов раз в секунду
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)
    # связываем кнопки с функциями
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_button.triggered.connect(server_config)
    # запуск  GUI
    server_app.exec_()


if __name__ == '__main__':
    main()
