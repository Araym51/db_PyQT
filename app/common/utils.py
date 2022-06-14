import json
from .constants import MAX_PACKAGE_LENGHT, ENCODING
from .decos import log


@log
def recieve_message(client):
    """
    общая функция для приема сообщений.
    Принимает байтовую строку, декодирует в json (кодировка utf-8)
    :param client:
    :return: json словарь
    """
    byte_response = client.recv(MAX_PACKAGE_LENGHT)  # получаем байтовую строку
    if isinstance(byte_response, bytes):  # проверям, входные данные
        json_response = byte_response.decode(ENCODING)  # декодируем в utf-8
        response = json.loads(json_response)  # перегоняем данные в словарь
        if isinstance(response, dict): # если получился словарь - возвращаем его в response
            return response
        raise ValueError
    raise ValueError


@log
def send_message(sock, message):
    """
    Функция для отправки сообщения.
    Декодирует сообщение в формат json и отправляет его
    :param sock:
    :param message:
    :return:
    """
    json_message = json.dumps(message)
    encoded_message = json_message.encode(ENCODING)
    sock.send(encoded_message)
