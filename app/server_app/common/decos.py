import socket
import sys
import logging

sys.path.append('../')
import loging.server_conf_log



# определяем, какой логгер использовать
LOGGER = logging.getLogger('server')


def log(func_to_log):
    '''
    Декоратор логирует вызововы функций.
    Сохраняет события типа debug, содержащие
    информацию о имени вызываемой функиции, параметры с которыми
    вызывается функция, и модуль, вызывающий функцию.
    '''
    def log_writer(*args, **kwargs):
        info = func_to_log(*args, **kwargs)
        LOGGER.debug(f'вызвана функция {func_to_log.__name__} с параметрами {args}, {kwargs}.'
                     f'Вызов из модуля {func_to_log.__module__}.'
                     )
        return info

    return log_writer


def login_required(func):
    """
    Декоратор проверяет, авторизован ли пользователь.
    Проверяет, что проверяемый объект сокета находится в списке авторизованных клиентов.
    За исключением запросов на авторизацию.
    Если клиент не авторизован, генерирует исключение TypeError
    """
    def validate(*args, **kwargs):
        from server.core import MessageProcessor
        from common.constants import ACTION, PRESENCE
        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    # Проверяем, что данный сокет есть в списке names класса MessageProcessor
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True
                    # Теперь надо проверить, что передаваемые аргументы не presence
                    # сообщение. Если presense, то разрешаем
                for arg in args:
                    if isinstance(arg, dict):
                        if ACTION in arg and arg[ACTION] == PRESENCE:
                            found = True
                    # Если не авторизован и не сообщение начала авторизации, то вызываем исключение.
                if not found:
                    raise TypeError
            return func(*args, **kwargs)

    return validate
