import logging

"""Постоянные настройки для сервера"""

# Порт для сетевого взаимодействия


SERVER_PORT = 8888

# ip адрес сервера
SERVER_IP = '127.0.0.1'

# максимальная очередь подключений
MAX_CONNECTIONS = 5

# максимальный размер пакета:
MAX_PACKAGE_LENGHT = 1024

# Кодировка
ENCODING = 'utf-8'

# Ключи для JSON instant messaging
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'sender'
DESTINATION = 'to'

# дополнительные ключи
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'message text'
EXIT = 'exit'

# уровень логированрия:
LOGGING_LEVEL = logging.DEBUG

# ответы
RESPONSE_200 = {RESPONSE: 200}
RESPONSE_400 = {
    RESPONSE:400,
    ERROR: None
}