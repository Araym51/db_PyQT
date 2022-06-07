import argparse
import sys
import os
import logging
from Crypto.PublicKey import RSA

from common.errors import ServerError
from app.common.decos import log
from common.constants import SERVER_IP, SERVER_PORT
from PyQt5.QtWidgets import QApplication, QMessageBox

from client.start_dialog import UserNameDialog
from client.main_window import ClientMainWindow
from client.transport import ClientTransport
from client.database import ClientDatabase

# инициализация логгера
CLIENT_LOGGER = logging.getLogger('client')


@log
def arg_parser():
    """
    парсер аргументов коммандной строки
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=SERVER_IP, nargs='?')
    parser.add_argument('port', default=SERVER_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_ip = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    client_passwd = namespace.password

    if not 1023 < server_port < 65536:
        CLIENT_LOGGER.critical(f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
                               f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)

    return server_ip, server_port, client_name, client_passwd



if __name__ == '__main__':
    # получаем параметры для сокета
    server_ip, server_port, client_name, client_password = arg_parser()
    CLIENT_LOGGER.debug(f'Аргументы получены. Клиент {client_name} запустился с параметрами {server_ip}: {server_port}')
    # запуск клиенсткого приложения
    client_app = QApplication(sys.argv)
    # запрашиваем имя пользователя
    start_dialog = UserNameDialog()
    if not client_name or not client_password:
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_password = start_dialog.client_password.text()
            CLIENT_LOGGER.debug(f'Username = {client_name}, password = {client_password}')
            del start_dialog
        else:
            exit(0)

    CLIENT_LOGGER.info(f'Запущен клиент с параметрами {server_ip} : {server_port}, имя пользователя: {client_name}')
    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())
    database = ClientDatabase(client_name)

    CLIENT_LOGGER.debug(f'Keys loaded')
    # Создаем объект ДБ
    database = ClientDatabase(client_name)
    # Создаем и запускаем транспорт
    try:
        transport = ClientTransport(
            server_port,
            server_ip,
            database,
            client_name,
            client_password,
            keys
        )
        CLIENT_LOGGER.debug(f'транспорт для {client_name} готов')
    except ServerError as error:
        message = QMessageBox()
        message.critical(start_dialog, 'Ошибка сервера', error.text)
        exit(1)

    transport.setDaemon(True)
    transport.start()

    del start_dialog
    # запуск графического интерфейса
    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат программа. Привет {client_name}!')
    client_app.exec_()

    # при закрытии программы, рвем соединение
    transport.transport_shutdown()
    transport.join()
