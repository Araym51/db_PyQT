import argparse
import sys

from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from client.transport import ClientTransport
from common.constants import *
import logging
from app.common.errors import ServerError
from logging_deco import log
from client.database import ClientDatabase
from PyQt5.QtWidgets import QApplication

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
    namespace = parser.parse_args(sys.argv[1:])
    server_ip = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < server_port < 65536:
        CLIENT_LOGGER.critical(f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
                               f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)

    return server_ip, server_port, client_name



if __name__ == '__main__':
    # получаем параметры для сокета
    server_ip, server_port, client_name = arg_parser()
    # запуск клиенсткого приложения
    client_app = QApplication(sys.argv)
    # запрашиваем имя пользователя
    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    CLIENT_LOGGER.info(f'Запущен клиент с параметрами {server_ip} : {server_port}, имя пользователя: {client_name}')

    database = ClientDatabase(client_name)

    try:
        transport = ClientTransport(server_port, server_ip, database, client_name)
    except ServerError as error:
        print(error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат программа. Привет {client_name}!')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()
