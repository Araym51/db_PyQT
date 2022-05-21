import logging
logger = logging.getLogger('server')

# дескриптор описания порта
class Port:
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
