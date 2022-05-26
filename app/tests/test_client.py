import sys
import os
sys.path.append(os.path.join(os.getcwd(), '..'))
import unittest
from app.common.constants import TIME, ACTION, PRESENCE, USER, ACCOUNT_NAME, RESPONSE, ERROR
from app.client_app import create_presence, process_answer

class TestClient(unittest.TestCase):
    """тестирование клиентского приложения"""
    def test_presence(self):
        """проверяем работу функции присутствия"""
        presence = create_presence()
        presence[TIME] = 10.01
        self.assertEqual(presence, {ACTION: PRESENCE, TIME: 10.01, USER:{ACCOUNT_NAME: 'Guest'}})

    def test_200_answer(self):
        """проверяем удачное соединение"""
        self.assertEqual(process_answer({RESPONSE: 200}), '200 : OK')

    def test_400_notfound(self):
        """проверяем ошибку соединения"""
        self.assertEqual(process_answer({RESPONSE: 400, ERROR: 'Bad Request'}), '400 : Bad Request')

    def test_no_response(self):
        """проверяем ошибку декодирования"""
        self.assertRaises(ValueError, process_answer, {ERROR: 'Bad Request'})

if __name__ == '__main__':
    unittest.main()