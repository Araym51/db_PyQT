"""Возможные ошибки"""

class ReqFieldMissingError(Exception):
    """Отсутствует обязательное поле в принятом словаре"""
    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'В принятом словаре отуствтвует обязательное поле {self.missing_field}'


class IncorrectDataRecievedError(Exception):
    """получение некорректных данных из сокета"""
    def __str__(self):
        return 'Принято некорректное сообщение от клиента'


class ServerError(Exception):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


class NonDictInputError(Exception):
    def __str__(self):
        return 'Аргумент функции должен быть словарем'
