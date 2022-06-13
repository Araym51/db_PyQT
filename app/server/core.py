import sys
import threading
import logging
import select
import socket
import json
import hmac
import binascii
import os

sys.path.append('../')
from common.metaclasses import ServerMarker
from common.descriptors import Port
from common.constants import ACCOUNT_NAME, MAX_CONNECTIONS, DESTINATION, SENDER, ACTION, PRESENCE, TIME, USER, \
    MESSAGE, MESSAGE_TEXT, RESPONSE_200, ERROR, RESPONSE_400, GET_CONTACTS, RESPONSE_202, LIST_INFO, ADD_CONTACT, \
    REMOVE_CONTACT, USERS_REQUEST, PUBLIC_KEY_REQUEST, RESPONSE_511, DATA, RESPONSE, PUBLIC_KEY, RESPONSE_205, EXIT
from common.utils import send_message, recieve_message
from common.decos import login_required

SERVER_LOGGER = logging.getLogger('server')


class MessageProcessor(threading.Thread):
    """
    Основной класс сервера. Принимает соединения, словари - пакеты от клиентов.
    Обрабатывает поступающие сообщения.
    Работает отдельным потоком.
    """
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        # ip и порт
        self.addr = listen_address
        self.port = listen_port

        # база данных
        self.database = database

        # сокет через который работает скрипт
        self.sock = None
        # клиенты
        self.clients = []

        # сокеты
        self.listen_sockets = None
        self.error_sockets = None

        # флаг продолжения работы:
        self.running = True

        # словарь имен и сопоставленные им сокеты
        self.names = dict()

        super().__init__()

    def run(self):
        """
        основной цикл потока
        """
        self.init_socket()

        # основной цикл сервера
        while self.running:
            # ждем клиентов
            try:
                client, client_adress = self.sock.accept()
            except OSError:
                pass
            else:
                SERVER_LOGGER.info(f'Установлено соединение с ПК {client_adress}')
                client.settimeout(5)
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            # Проверяем на наличие ждущих клиентов
            try:
                if self.clients:
                    recv_data_lst, self.listen_sockets, self.error_sockets = select.select(
                        self.clients, self.clients, [], 0)
            except OSError as error:
                SERVER_LOGGER.error(f'Ошибка работы с сокетами: {error.errno}')

            # принимаем сообщение, если ошибка - исключаем клиента
            if recv_data_lst:
                for clients_with_message in recv_data_lst:
                    try:
                        self.process_client_message(recieve_message(clients_with_message), clients_with_message)
                    except (OSError, json.JSONDecodeError, TypeError) as error:
                        SERVER_LOGGER.debug(f'Ошибка приема сообщения', exc_info=error)
                        self.remove_client(clients_with_message)

    def remove_client(self, client):
        """
        Метод обрабатывает клиента с которым оборвана связь.
        Ищет клиента и удаляет его сз списков и базы
        """
        SERVER_LOGGER.info(f'Клиент {client.getpeername()} отключен от сервера')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def init_socket(self):
        """"
        метод инициализатор сокета
        """
        SERVER_LOGGER.info(
            f'Запущен сервер, порт для подключений: {self.port}, адрес с которого принимаются подключения: {self.addr}. Если адрес не указан, принимаются соединения с любых адресов.')
        # Поготовка сокета
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        # слушаем сокет
        self.sock = transport
        self.sock.listen(MAX_CONNECTIONS)

    def process_message(self, message):
        """метод отправки сообщений клиенту"""
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]
        ] in self.listen_sockets:
            try:
                send_message(self.names[message[DESTINATION]], message)
                SERVER_LOGGER.info(
                    f'Отправлено сообщение пользователю {message[DESTINATION]} от пользователя {message[SENDER]}.')
            except OSError:
                self.remove_client(message[DESTINATION])
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in self.listen_sockets:
            SERVER_LOGGER.error(
                f'Связь с клиентом {message[DESTINATION]} была потеряна. Соединение закрыто, доставка невозможна.')
            self.remove_client(self.names[message[DESTINATION]])
        else:
            SERVER_LOGGER.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, отправка сообщения невозможна.')

    # @login_required
    def process_client_message(self, message, client):
        """метод обработчик поступающих сообщений"""
        SERVER_LOGGER.debug(f"Разбор сообщения от клиента: {message}")
        # если сообщение о присутствии - принимаем и отвечаем
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            # Если сообщение о присутствии то вызываем функцию авторизации.
            self.autorize_user(message, client)

        # Если это сообщение, то отправляем его получателю.
        elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message and self.names[message[SENDER]] == client:
            if message[DESTINATION] in self.names:
                self.database.process_message(
                    message[SENDER], message[DESTINATION])
                self.process_message(message)
                try:
                    send_message(client, RESPONSE_200)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Пользователь не зарегистрирован на сервере.'
                try:
                    send_message(client, response)
                except OSError:
                    pass
            return

        # Если клиент выходит
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message \
                 and self.names[message[ACCOUNT_NAME]] == client:
            self.remove_client(client)

        # Если это запрос контакт-листа
        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        # Если это добавление контакта
        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_200)
            except OSError:
                self.remove_client(client)

        # Если это удаление контакта
        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_200)
            except OSError:
                self.remove_client(client)

        # Если это запрос известных пользователей
        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0]
                                   for user in self.database.users_list()]
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        # Если это запрос публичного ключа пользователя
        elif ACTION in message and message[ACTION] == PUBLIC_KEY_REQUEST and ACCOUNT_NAME in message:
            response = RESPONSE_511
            response[DATA] = self.database.get_pubkey(message[ACCOUNT_NAME])
            # может быть, что ключа ещё нет (пользователь никогда не логинился,
            # тогда шлём 400)
            if response[DATA]:
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Нет публичного ключа для данного пользователя'
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)

        # Иначе отдаём Bad request
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

    def autorize_user(self, message, sock):
        """
        метод отвечает за авторизацию пользователей,
        Если имя пользователя занято - возвращает 400
        """
        SERVER_LOGGER.debug(f"Авторизация для {message[USER]}")
        if message[USER][ACCOUNT_NAME] in self.names.keys():
            response = RESPONSE_400
            response[ERROR] = 'Имя пользователя уже занято'
            try:
                SERVER_LOGGER.debug(f'Имя пользователя занято, отвечаем {response}')
                send_message(sock, response)
            except OSError:
                SERVER_LOGGER.debug('OS error')
                pass
            self.clients.remove(sock)
            sock.close()
        elif not self.database.check_user(message[USER][ACCOUNT_NAME]):
            response = RESPONSE_400
            response[ERROR] = 'Пользователь не зарегистрирован'
            try:
                SERVER_LOGGER.debug(f'Неизвестный пользователь, отвечаею: {response}')
                send_message(sock, response)
            except OSError:
                pass
        else:
            SERVER_LOGGER.debug('Корректное имя пользователя, проверка пароля')
            # Иначе отвечаем 511 и проводим процедуру авторизации. Словарь - заготовка
            message_auth = RESPONSE_511
            # Набор байтов в hex представлении
            random_str = binascii.hexlify(os.urandom(64))
            # В словарь байты нельзя, декодируем (json.dumps -> TypeError)
            message_auth[DATA] = random_str.decode('ascii')
            # Создаём хэш пароля и связки с рандомной строкой, сохраняем серверную версию ключа
            hash = hmac.new(self.database.get_hash(message[USER][ACCOUNT_NAME]), random_str, 'MD5')
            digest = hash.digest()
            SERVER_LOGGER.debug(f'Авторизация = {message_auth}')
            try:
                # обмен с клиентом
                send_message(sock, message_auth)
                answer = recieve_message(sock)
            except OSError as error:
                SERVER_LOGGER.debug("Ошибка при авторизации", exc_info=error)
                sock.close()
                return
            client_digest = binascii.a2b_base64((answer[DATA]))
            # если ответ пользователя корректный, добавляем его в список пользователей
            if RESPONSE in answer and answer[RESPONSE] == 511 and hmac.compare_digest(digest, client_digest):
                self.names[message[USER][ACCOUNT_NAME]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    send_message(sock, RESPONSE_200)
                except OSError:
                    self.remove_client(message[USER][ACCOUNT_NAME])
                # добавляем пользователя в список активных, если у него изменился ключ сохраняем новый
                self.database.user_login(
                message[USER][ACCOUNT_NAME],
                client_ip,
                client_port,
                message[USER][PUBLIC_KEY]
                )
            else:
                response = RESPONSE_400
                response[ERROR] = 'Неверный пароль.'
                try:
                    send_message(sock, response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def service_update_lists(self):
        """метод отправляет сервисное сообщение '205' клиентам."""
        for client in self.names:
            try:
                send_message(self.names[client], RESPONSE_205)
            except OSError:
                self.remove_client(self.names[client])
