import ipaddress
import logging
logger = logging.getLogger('server')


class Port:
    """
    дескриптор контроля значений порта порта
    """
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            logger.critical(f'попытка запуска сервера с неподходящим портом {value}.'
                            f'допустимы значения от 1024 до 65535')
            exit(1)
        # Если порт в допустимом диапазоне, добавляем его в список атрибутов экземпляра
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        # owner - имя класса
        # name - порт
        self.name = name


class Host:
    """
    дескриптор контроля значений ip адресов
    """
    def __set__(self, instance, value):
        if value:
            try:
                ip = ipaddress.ip_address(value)
            except ValueError as error:
                logger.critical(f'Введен неправильный IP адрес {error}')
                exit(1)
            instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
