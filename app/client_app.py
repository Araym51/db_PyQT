import argparse
import logging
import sys
import json
import socket
import threading
import time
from common.constants import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, SERVER_PORT, SERVER_IP, \
    MESSAGE, SENDER, MESSAGE_TEXT, EXIT, DESTINATION
from common.utils import recieve_message, send_message
import logging
import loging.client_conf_log
from errors import ReqFieldMissingError, ServerError, IncorrectDataRecievedError
from logging_deco import log
from metaclasses import ClientMarker

# инициализация логгера
CLIENT_LOGGER = logging.getLogger('client')

# класс формирует и отправляет сообщения на сервер и взаимодействует с пользователем
class ClientSender(threading.Thread, metaclass=ClientMarker):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    # Сообщение о выходе:
    def exit_message(self):
        """Функция создает сообщение о выходе из программы"""
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    # Функция запрашивает, кому отправить сообщение, и отправляет полученные данные на сервер
    def create_message(self):
        to_user = input("Введите получателя сообщения: ")
        message = input("Введите сообщение: ")
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        CLIENT_LOGGER.debug(f'Сформировано сообщение: {message_dict}')
        try:
            send_message(self.sock, message_dict)
            CLIENT_LOGGER.info(f'Отправлено сообщение пользователю {to_user}')
        except:
            CLIENT_LOGGER.critical(f'Потеряно соединение с сервером')
            sys.exit(1)

    # Функция для взаимодествия с пользователем, запрашивает команда, отправляет сообщения
    def run(self):
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                try:
                    send_message(self.sock, self.exit_message())
                except:
                    pass
                print('завершение работы')
                CLIENT_LOGGER.info(f'{self.account_name} завершил работу')
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    # Функция выводящяя справку по использованию
    def print_help(self):
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

# класс принимает сообщения с сервера. Выводит принятые сообщения в консоль
class ClientReader(threading.Thread, metaclass=ClientMarker):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    # цикл приема сообщений. Завершается при потере соединения
    def run(self):
        while True:
            try:
                message = recieve_message(self.sock)
                if ACTION in message and message[ACTION] == MESSAGE and \
                        SENDER in message and DESTINATION in message \
                        and MESSAGE_TEXT in message and message[DESTINATION] == self.account_name:
                    print(f'\n Получено сообщение от пользователя {message[SENDER]}:'
                          f'\n {message[MESSAGE_TEXT]}')
                    CLIENT_LOGGER.info(f'\n Получено сообщение от пользователя {message[SENDER]}:'
                                       f'\n {message[MESSAGE_TEXT]}')
                else:
                    CLIENT_LOGGER.error(f'принято некорректное сообщение от сервера {message}')
            except IncorrectDataRecievedError:
                CLIENT_LOGGER.error(f'Не удалось декодировать сообщение')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                CLIENT_LOGGER.critical(f'потеряно соединение с сервером')
                break


@log
def create_presence(account_name):
    """
    функция сообщает серверу о присутствии account_name
    """
    presence_message = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение для {account_name}')
    # print(f'Сформировано {PRESENCE} сообщение для {account_name}')
    return presence_message


@log
def process_answer(message):
    """
    функция разбирает ответ сервера
    :param message:
    :return:
    """
    CLIENT_LOGGER.debug(f'расшифровка сообщения от сервера: {message}')
    # print(f'расшифровка сообщения от сервера: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


@log
def arg_parser():
    """
    парсер аргументов коммандной строки
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=SERVER_IP, nargs='?')
    parser.add_argument('port', default=SERVER_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_ip = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < server_port < 65536:
        CLIENT_LOGGER.critical(f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
                               f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)

    return server_ip, server_port, client_name


def main():
    # прветственное сообщение при запуске:
    print('клиентский модуль консольного мессенджера')

    # загружаем параметры переданные в коммандной строке
    server_adress, server_port, client_name = arg_parser()

    if not client_name:
        client_name = input('Введите имя пользователя: ')

    CLIENT_LOGGER.info(f'Запущен клиент с параметрами: '
                       f'адрес сервера: {server_adress}, '
                       f' порт сервера: {server_port},'
                       f' имя пользователя: {client_name}')

    try:
        CLIENT = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        CLIENT.connect((server_adress, server_port))
        send_message(CLIENT, create_presence(client_name))
        answer = process_answer(recieve_message(CLIENT))
        CLIENT_LOGGER.info(f'становлено соединение с сервером. Ответ от сервера: {answer}')
        print(f'установлено соединение с сервером {client_name}')
    except json.JSONDecodeError:
        CLIENT_LOGGER.error('Не удалось декодировать json строку')
        print(f'Не удалось декодировать json строку')
        sys.exit(1)
    except ServerError as error_ans:
        CLIENT_LOGGER.error(f'При установке соединения сервер вернул ошибку: {error_ans.text}')
        print(f'При установке соединения сервер вернул ошибку: {error_ans.text}')
        sys.exit(1)
    except ReqFieldMissingError as error_mis:
        CLIENT_LOGGER.error(f'тсутствует необходимое поле в ответе от сервера: {error_mis.missing_field}')
        print(f'тсутствует необходимое поле в ответе от сервера: {error_mis.missing_field}')
        sys.exit(1)
    except ConnectionRefusedError:
        CLIENT_LOGGER.critical(f'Не удалось подключиться к серверу {server_adress}:{server_port}, '
                               f'конечный компьютер отверг запрос на подключение.')
        print(f'Не удалось подключиться к серверу {server_adress}:{server_port}, '
                               f'конечный компьютер отверг запрос на подключение.')
        sys.exit(1)
    else:
        # если есть соединение с сервером, запускаем процесс приема сообщений
        receiver = ClientReader(client_name, CLIENT)
        receiver.daemon = True
        receiver.start()

        # запускаем отправку сообщений и взаимодействие с пользователем.
        user_interface = ClientSender(client_name, CLIENT)
        user_interface.daemon = True
        user_interface.start()
        CLIENT_LOGGER.debug('Запущены процессы')

        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
