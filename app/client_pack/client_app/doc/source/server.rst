Server module
=================================================

Серверный модуль приложения. Обрабатывает словари - сообщения, хранит публичные ключи клиентов.

Использование:

Модуль подерживает аргументы командной стороки:

1. -p - Порт на котором принимаются соединения
2. -a - Адрес с которого принимаются соединения.
3. --no_gui Запуск только основных функций, без графической оболочки.

* В режиме без графического интерфейса поддерживается только 1 команда: exit - завершение работы.

Примеры использования:

``python server.py -p 8888``

*Запуск сервера на порту 8888*

``python server.py -a localhost``

*Запуск сервера принимающего только соединения с localhost*

``python server.py --no-gui``

*Запуск без графической оболочки*

server.py
~~~~~~~~~

Запускаемый модуль,содержит парсер аргументов командной строки (в т.ч. и из *.ini файла)
и функционал инициализации приложения.

server. **arg_parser** ()
    Парсер аргументов командной строки, возвращает кортеж из 4 элементов:

	* адрес с которого принимать соединения
	* порт
	* флаг запуска GUI

server. **config_load** ()
    Функция загрузки параметров конфигурации из ini файла.
    В случае отсутствия файла задаются параметры по умолчанию.

core.py
~~~~~~~~~~~

.. autoclass:: server.core.MessageProcessor
	:members:

server_database.py
~~~~~~~~~~~

.. autoclass:: server.server_database.ServerStorage
	:members:

main_window.py
~~~~~~~~~~~~~~

.. autoclass:: server.main_window.MainWindow
	:members:

add_user.py
~~~~~~~~~~~

.. autoclass:: server.add_user.RegisterUser
	:members:

remove_user.py
~~~~~~~~~~~~~~

.. autoclass:: server.remove_user.DelUserDialog
	:members:

config_window.py
~~~~~~~~~~~~~~~~

.. autoclass:: server.config_window.ConfigWindow
	:members:

stat_window.py
~~~~~~~~~~~~~~~~

.. autoclass:: server.stat_window.StatWindow
	:members: