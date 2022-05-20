import sys
import logging
import loging.client_conf_log
import loging.server_conf_log
import traceback
import inspect

# определяем, какой логгер использовать
if sys.argv[0].find('client') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


def log(func_to_log):
    def log_writer(*args, **kwargs):
        info = func_to_log(*args, **kwargs)
        LOGGER.debug(f'вызвана функция {func_to_log.__name__} с параметрами {args}, {kwargs}.'
                     f'Вызов из модуля {func_to_log.__module__}.'
                     # f'вызов из функции {traceback.format_stack()[0].strip().split()[-1]}'
                     # f'вызов из функции {inspect.stack()[1][3]}'
                     )
        return info

    return log_writer
