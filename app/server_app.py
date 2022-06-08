import argparse
import os.path
import sys
import threading
import logging
import configparser
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from server.main_window import MainWindow
from server.core import MessageProcessor
from common.constants import SERVER_PORT
from common.decos import log
from server.server_database import ServerStorage


SERVER_LOGGER = logging.getLogger('server')

new_connection = False
conflag_lock = threading.Lock()


@log
def args_reader(default_port, default_address):
    """
    Чтение и передача параметров с коммандной строки
    """
    SERVER_LOGGER.debug(f'Инициализация парсера аргументов коммандной строки: {sys.argv}')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    parser.add_argument('--no_gui', action='store_true')
    namespace = parser.parse_args(sys.argv[1:])
    serv_adress = namespace.a
    serv_port = namespace.p
    gui_flag = namespace.no_gui
    SERVER_LOGGER.debug('Аргументы успешно загружены.')
    return serv_adress, serv_port, gui_flag



def config_load():
    """парсер конфигурационного файла server.ibi"""
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    # Читаем конфиг, если всё хорошо - запускаем.
    # Иначе берем параметры по умолчанию из констант
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(SERVER_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config


def main():
    """
    основная функция работы сервера
    """
    config = config_load()

    # Загрузка параметров с коммандной строки, если нет параметро, задаем значения по умолчанию
    listen_address, listen_port, gui_flag = args_reader(
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    # инициализация БД
    database = ServerStorage(os.path.join(
        config['SETTINGS']['Database_path'],
        config['SETTINGS']['Database_file']
    ))

    # Создание экземпляра класса - сервера и его запуск:
    server = MessageProcessor(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    # Если  указан параметр без GUI то запускаем простенький обработчик консольного ввода
    if gui_flag:
        while True:
            command = input('Введите exit для завершения работы сервера.')
            if command == 'exit':
                # Если выход, то завршаем основной цикл сервера.
                server.running = False
                server.join()
                break
    # если не указан флаг gui запускается обработчик консольного ввода
    else:
        # запуск графического окружения сервера
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(database, server, config)

        # запуск gui
        server_app.exec_()

        # при закрытии окна - останавливаем сервер
        server.running = False


if __name__ == '__main__':
    main()
