"""конфигурация логов для сервера"""

import sys
import os
import logging
import logging.handlers
from common.constants import LOGGING_LEVEL # выглядит как ошибка, но благодаря sys.path.append('../') работает
sys.path.append('../')

# формат логов для сервера
SERVER_FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

# файл для логов
PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'server.log')

# потоки вывода логов
STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(SERVER_FORMATTER)
STREAM_HANDLER.setLevel(logging.ERROR)
SERVER_LOGS = logging.handlers.TimedRotatingFileHandler(PATH, encoding='utf-8', interval=1, when='D')
SERVER_LOGS.setFormatter(SERVER_FORMATTER)

# настройка регистратора
LOGGER = logging.getLogger('server')
LOGGER.addHandler(STREAM_HANDLER)
LOGGER.addHandler(SERVER_LOGS)
LOGGER.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    LOGGER.critical('Критическая ошибка')
    LOGGER.error('Ошибка')
    LOGGER.debug('Отладочная информация')
    LOGGER.info('Информационное сообщение')
