import binascii
import hashlib
import hmac
import socket
import time
import logging
import json
import threading
from PyQt5.QtCore import pyqtSignal, QObject

import sys

from app.common.constants import PUBLIC_KEY, DATA, RESPONSE_511, PUBLIC_KEY_REQUEST

sys.path.append('../')
from common.utils import send_message, recieve_message
from common.constants import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, MESSAGE, SENDER, \
    DESTINATION, MESSAGE_TEXT, GET_CONTACTS, LIST_INFO, USERS_REQUEST, ADD_CONTACT, REMOVE_CONTACT, EXIT
from common.errors import ServerError

# инициализация логгера
CLIENT_LOGGER = logging.getLogger('client')
sock_lock = threading.Lock()

class ClientTransport(threading.Thread, QObject):
    # сигналы о новом сообщении и потере соединения
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username, passwd, keys):
        # конструктор предка
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.username = username
        self.transport = None
        self.password = passwd
        self.keys = keys
        # устанавливаем соединение
        self.connection_init(port, ip_address)
        # Обновление таблицы известных пользователей и контактов
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as error:
            if error.errno:
                CLIENT_LOGGER.critical(f'Потеряно соединение с сервером. 40')
                raise ServerError('Потеряно соединение с сервером!')
            CLIENT_LOGGER.error('Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            CLIENT_LOGGER.critical(f'Потеряно соединение с сервером. 44')
            raise ServerError('Потеряно соединение с сервером!')
        # флаг для продолжения работы сокета
        self.running = True

    # инициализация соединения с сервером
    def connection_init(self, port, ip):
        # инициализация сокета
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # таймаут для освобождения сокета
        self.transport.settimeout(5)

        connected = False
        # 5 попыток чтобы соединится с сервером
        for i in range(5):
            CLIENT_LOGGER.info(f"Попытка подключения к серверу № {i+1}")
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                CLIENT_LOGGER.error('Connection aborted! -65')
                pass
            else:
                connected = True
                CLIENT_LOGGER.debug('Connection established!')
                break
            time.sleep(1)
        #если не присоединился - исключение
        if not connected:
            CLIENT_LOGGER.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')

        CLIENT_LOGGER.debug('Установлено соединение с сервером')

        # продцедура авторизации
        passwd_bytes = self.password.encode('utf-8')
        salt = self.username.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)

        pubkey = self.keys.publickey().export_key().decode('ascii')

        CLIENT_LOGGER.debug(f'Passwd hash ready: {passwd_hash_string}')

        with sock_lock:
            presense = {
                ACTION: PRESENCE,
                TIME: time.time(),
                USER: {
                    ACCOUNT_NAME: self.username,
                    PUBLIC_KEY: pubkey
                }
            }
            CLIENT_LOGGER.debug(f"Presense message = {presense}")
            # Отправляем серверу приветственное сообщение.
            try:
                send_message(self.transport, presense)
                ans = recieve_message(self.transport)
                CLIENT_LOGGER.debug(f'Server response = {ans}.')
                # Если сервер вернул ошибку, бросаем исключение.
                if RESPONSE in ans:
                    if ans[RESPONSE] == 400:
                        raise ServerError(ans[ERROR])
                    elif ans[RESPONSE] == 511:
                        # Если всё нормально, то продолжаем процедуру
                        # авторизации.
                        ans_data = ans[DATA]
                        hash = hmac.new(passwd_hash_string, ans_data.encode('utf-8'), 'MD5')
                        digest = hash.digest()
                        my_ans = RESPONSE_511
                        my_ans[DATA] = binascii.b2a_base64(
                            digest).decode('ascii')
                        send_message(self.transport, my_ans)
                        self.process_server_ans(recieve_message(self.transport))
            except (OSError, json.JSONDecodeError) as err:
                CLIENT_LOGGER.debug(f'Connection error.', exc_info=err)
                raise ServerError('Сбой соединения в процессе авторизации.')

    # Функция бработчик сообщений от сервера. Если ошибка, генерирует исключение.
    def process_server_ans(self, message):
        CLIENT_LOGGER.debug(f'Разбор сообщения от сервера: {message}')

        # Если это подтверждение чего-либо
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return
            elif message[RESPONSE] == 400:
                raise ServerError(f'{message[ERROR]}')
            elif message[RESPONSE] == 205:
                self.user_list_update()
                self.contacts_list_update()
                self.message_205.emit()
            else:
                CLIENT_LOGGER.error(
                    f'Принят неизвестный код подтверждения {message[RESPONSE]}')

        # Если это сообщение от пользователя добавляем в базу, даём сигнал о
        # новом сообщении
        elif ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                and MESSAGE_TEXT in message and message[DESTINATION] == self.username:
            CLIENT_LOGGER.debug(
                f'Получено сообщение от пользователя {message[SENDER]}:{message[MESSAGE_TEXT]}')
            self.new_message.emit(message)

    # Функция обновления контакт-листа
    def contacts_list_update(self):
        CLIENT_LOGGER.debug(f'Запрос контакт листа для пользователся {self.name}')
        req = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.username
        }
        CLIENT_LOGGER.debug(f'Сформирован запрос {req}')
        with sock_lock:
            send_message(self.transport, req)
            ans = recieve_message(self.transport)
        CLIENT_LOGGER.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for contact in ans[LIST_INFO]:
                self.database.add_contact(contact)
        else:
            CLIENT_LOGGER.error('Не удалось обновить список контактов.')


    # Функция обновления таблицы известных пользователей.
    def user_list_update(self):
        CLIENT_LOGGER.debug(f'Запрос списка известных пользователей {self.username}')
        req = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with sock_lock:
            send_message(self.transport, req)
            ans = recieve_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            self.database.add_users(ans[LIST_INFO])
        else:
            CLIENT_LOGGER.error('Не удалось обновить список известных пользователей.')

    def key_request(self, user):
        CLIENT_LOGGER.debug(f'Запрос публичного ключа для {user}')
        request = {
            ACTION: PUBLIC_KEY_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: user
        }
        with sock_lock:
            send_message(self.transport, request)
            answer = recieve_message(self.transport)
        if RESPONSE in answer and answer[RESPONSE] == 511:
            return answer[DATA]
        else:
            CLIENT_LOGGER.error(f'Не удалось получить ключ для {user}')

    # функция сообщает на сервер о добавлении контакта
    def add_contact(self, contact):
        CLIENT_LOGGER.debug(f'Создан контакт: {contact}')
        request = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with sock_lock:
            send_message(self.transport, request)
            self.process_server_ans(recieve_message(self.transport))

    # Удаление клиента на сервере
    def remove_contact(self, contact):
        CLIENT_LOGGER.debug(f'Удаление контакта {contact}')
        request = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with sock_lock:
            send_message(self.transport, request)
            self.process_server_ans(recieve_message(self.transport))

    # закрытие соединения, сообщает о выходе
    def transport_shutdown(self):
        self.running = False
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with sock_lock:
            try:
                send_message(self.transport, message)
            except OSError:
                pass
        CLIENT_LOGGER.debug('Транспорт завершает работу.')
        time.sleep(0.5)

    # отправка сообщения на сервер
    def send_message(self, to, message):
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with sock_lock:
            send_message(self.transport, message_dict)
            self.process_server_ans(recieve_message(self.transport))
            CLIENT_LOGGER.info(f'Отправлено сообщение для пользователя {to}')

    # и тут всё как завертелось
    def run(self):
        CLIENT_LOGGER.debug('Запущен процесс - приёмник собщений с сервера.')
        while self.running:
            # Отдыхаем секунду и снова пробуем захватить сокет.
            # если не сделать тут задержку, то отправка может достаточно долго
            # ждать освобождения сокета.
            time.sleep(1)
            message = None
            with sock_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = recieve_message(self.transport)
                except OSError as err:
                    if err.errno:
                        CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    CLIENT_LOGGER.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                finally:
                    self.transport.settimeout(5)

            # Если сообщение получено, то вызываем функцию обработчик:
            if message:
                CLIENT_LOGGER.debug(f'Принято сообщение с сервера: {message}')
                self.process_server_ans(message)
