import sys
import os
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))
from app.common.constants import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from app.server_app import process_client_message


class TestServer(unittest.TestCase):
    error_dict = {
        RESPONSE: 400,
        ERROR: 'bad request'
    }
    correct_dict = {RESPONSE: 200}

    def test_action_error(self):
        """отсутствует Action"""
        self.assertEqual(process_client_message({
            TIME: 4.04, USER: {ACCOUNT_NAME: 'Guest'}
        }), self.error_dict)

    def test_wrong_action(self):
        """wrong action"""
        self.assertEqual(process_client_message({
            ACTION: 'Wrong', TIME: '2.00', USER: {ACCOUNT_NAME: 'Guest'}
        }), self.error_dict)

    def test_wrong_time(self):
        """нет параметра время"""
        self.assertEqual(process_client_message({
            ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Guest'}
        }), self.error_dict)

    def test_no_user(self):
        """забыли передать пользователя"""
        self.assertEqual(process_client_message({
            {ACTION: PRESENCE, TIME: 4.04}
        }), self.error_dict)

    def test_unknow_user(self):
        """неизвестный пользователь"""
        self.assertEqual(process_client_message({
            ACTION: PRESENCE, TIME: 4.04, USER: {ACCOUNT_NAME: 'Egorka'}
        }), self.error_dict)

    def test_correct_response(self):
        """если всё хорошо"""
        self.assertEqual(process_client_message({
            ACTION: PRESENCE, TIME: 2.00, USER:{ACCOUNT_NAME: 'Guest'}
        }), self.correct_dict)


if __name__ == '__main__':
    unittest.main()
