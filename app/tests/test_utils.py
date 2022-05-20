import json

from ..common.constants import *
from ..common.utils import send_message, recieve_message
import unittest


class TestSock:
    """
    Тестовый класс для отправки и получения сообщений.
    На вход требуется словарь для работы с функциями
    """
    def __init__(self, test_data):
        """
        входные данные
        """
        self.test_data = test_data
        self.send_message = None
        self.get_message = None

    def send(self, test_message):
        """
        Функия для отправки закодированного сообщения
        """
        json_test_message = json.dumps(self.test_data)
        # кодирует сообщение в json формат
        self.send_message = json_test_message.encode(ENCODING)
        # данные для отправки:
        self.get_message = test_message

    def recv(self, max_len):
        """
        Функция получает и кодирует данные из сокета:
        """
        json_test_message = json.dumps(self.test_data)
        return json_test_message.encode(ENCODING)


class TestServer(unittest.TestCase):
    """
    класс для тестирования отправки и принятия сообщений
    """
    send_message = {
        ACTION: PRESENCE,
        TIME: 04.04,
        USER: {
            ACCOUNT_NAME: 'Guest'
        }
    }
    response_ok = {RESPONSE: 200}
    response_error = {
        RESPONSE: 400,
        ERROR: 'bad request'
    }

    def test_send_message(self):
        # создаем экземпляр тестового словаря
        test_sock = TestSock(self.send_message)
        # пытаемся отправить сообщение
        send_message(test_sock, self.send_message)
        # проверяем, успешно ли
        self.assertEqual(test_sock.send_message, test_sock.get_message)

    def test_get_message(self):
        test_sock_ok = TestSock(self.response_ok)
        test_sock_error = TestSock(self.response_error)
        # проверяем корректность расшифровки сообщения
        self.assertEqual(recieve_message(test_sock_ok), self.response_ok)
        # проверяем корректность расшифровки сообщения с ошибкой
        self.assertEqual(recieve_message(test_sock_error), self.response_error)



if __name__ == '__main__':
    unittest.main()
