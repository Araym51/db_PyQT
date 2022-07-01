Common package
=================================================

Пакет общих скриптов, использующихся в разных модулях проекта.

Скрипт decos.py
---------------

.. automodule:: common.decos
    :members:
	
Скрипт descriptors.py
---------------------

.. autoclass:: common.descriptors.Port
    :members:
   
Скрипт errors.py
---------------------
   
.. autoclass:: common.errors.ServerError
   :members:
   
Скрипт metaclasses.py
-----------------------

.. autoclass:: common.metaclasses.ServerMarker
   :members:
   
.. autoclass:: common.metaclasses.ClientMarker
   :members:
   
Скрипт utils.py
---------------------

common.utils. **get_message** (client)


    Общая функция для приема сообщений.
    Принимает байтовую строку, декодирует в json (кодировка utf-8)

common.utils. **send_message** (sock, message)


    Функция для отправки сообщения.
    Декодирует сообщение в формат json и отправляет его через сокет


Скрипт variables.py
---------------------

Содержит разные глобальные переменные проекта.