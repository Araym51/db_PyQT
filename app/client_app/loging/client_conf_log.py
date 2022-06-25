import sys
import os
import logging
sys.path.append('../')
from common.constants import LOGGING_LEVEL  # выглядит как ошибка, но благодаря sys.path.append('../') работает



# задаём форму вывода для логов:
CLIENT_LOG_FORMAT = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

# задаём файл для логов
PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'client.log')

# потоки вывода логов
STREAM_HANDLER = logging.StreamHandler(sys.stderr)
# Задаём формат
STREAM_HANDLER.setFormatter(CLIENT_LOG_FORMAT)
STREAM_HANDLER.setLevel(logging.ERROR)
# устанавливаем кодировку
LOG_FILE = logging.FileHandler(PATH, encoding='utf8')
LOG_FILE.setFormatter(CLIENT_LOG_FORMAT)

# настройки регистратора
LOGGER = logging.getLogger('client')
LOGGER.addHandler(STREAM_HANDLER)
LOGGER.addHandler(LOG_FILE)
LOGGER.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    LOGGER.critical('Критическая ошибка')
    LOGGER.error('Ошибка')
    LOGGER.debug('Отладочная информация')
    LOGGER.info('Информационное сообщение')
