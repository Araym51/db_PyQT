from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, Qt
import sys
import logging

sys.path.append('../')
from common.errors import ServerError
from client.add_contact import AddContactDialog
from client.del_contact import DelContactDialog
from client.main_window_conv import Ui_MainClientWindow

CLIENT_LOGGER = logging.getLogger('client')


# Главное окно
class ClientMainWindow(QMainWindow):
    def __init__(self, database, transport):
        super().__init__()
        self.database = database
        self.transport = transport

        # загрузка конфигурации окна дизайнера
        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        # exit
        self.ui.menu_exit.triggered.connect(qApp.exit)

        # send message
        self.ui.btn_send.clicked.connect(self.send_message)

        # add contact
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)

        # del contact
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)
        self.ui.menu_del_contact.triggered.connect(self.delete_contact_window)

        # доп атрибуты
        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None
        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

        # обработка 2х клика по листу контактов
        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)

        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    # деактивация полей ввода
    def set_disabled_input(self):
        self.ui.label_new_message.setText('Двойной клик для выбора адресата')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()

        self.ui.btn_clear.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

    # история сообшений
    def history_list_update(self):
        # сортируем по дате
        list_ = sorted(self.database.get_history(self.current_chat), key=lambda item: item[3])
        # создание модели по надобности
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)

        self.history_model.clear()
        lenght = len(list_)
        start_index = 0
        if lenght > 20:
            start_index = lenght - 20

        # заполняем модель записями, разделяем входящие и исходящие
        for i in range(start_index, lenght):
            item = list_[i]
            if item[1] == 'in':
                message = QStandardItem(f'Входящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                message.setEditable(False)
                message.setBackground(QBrush(QColor(255, 213, 213)))
                message.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(message)
            else:
                message = QStandardItem(f'Исходящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                message.setEditable(False)
                message.setTextAlignment(Qt.AlignRight)
                message.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(message)
        self.ui.list_messages.scrollToBottom()

    # выбор пользователя по 2х клику
    def select_active_user(self):
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        self.set_active_user()

    # установка активного собеседника
    def set_active_user(self):
        self.ui.label_new_message.setText(f'Введите сообщенние для {self.current_chat}:')
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)
        # история сообщений по требуемому пользователю
        self.history_list_update()

    # обновление контакт листа
    def clients_list_update(self):
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    # добавление контакта
    def add_contact_window(self):
        global select_dialog
        select_dialog = AddContactDialog(self.transport, self.database)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    # обработка добавления контакта
    def add_contact_action(self, item):
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    # добавление контакта в БД
    def add_contact(self, new_contact):
        try:
            self.transport.add_contact(new_contact)
        except ServerError as error:
            self.messages.critical(self, 'Ошибка сервера', error.text)
        except OSError as error:
            if error.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения! \n add_contact')
        else:
            self.database.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            CLIENT_LOGGER.info(f'Успешно добавлен контакт {new_contact}')
            self.messages.information(self, 'Успех', 'Контакт успешно добавлен.')

    # удаление контакта
    def delete_contact_window(self):
        global remove_dialog
        remove_dialog = DelContactDialog(self.database)
        remove_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    # обработка удаления контакта
    def delete_contact(self, item):
        selected = item.selector.currentText()
        try:
            self.transport.remove_contact(selected)
        except ServerError as error:
            self.messages.critical(self, 'Ошибка сервера', error.text)
        except OSError as error:
            if error.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.del_contact(selected)
            self.clients_list_update()
            CLIENT_LOGGER.info(f'Успешно удалён контакт {selected}')
            self.messages.information(self, 'Успех', 'Контакт успешно удалён.')
            item.close()
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    # отправка сообщения пользователю
    def send_message(self):
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not message_text:
            return
        try:
            self.transport.send_message(self.current_chat, message_text)
            pass
        except ServerError as error:
            self.messages.critical(self, 'Ошибка', error.text)
        except OSError as error:
            if error.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!') # todo тут падает... и в базу не сохраняет
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
            self.close()
        else:
            self.database.save_message(self.current_chat, 'out', message_text)
            CLIENT_LOGGER.debug(f'Отправлено сообщение для {self.current_chat}: {message_text}')
            self.history_list_update()

    # слот приема нового сообщения
    @pyqtSlot(str)
    def message(self, sender):
        if sender == self.current_chat:
            self.history_list_update()
        else:
            # проверка наличия пользователя в контактах
            if self.database.check_contact(sender):
                # при наличии, спрашиваем, хочет ли открыть чат, если нужно, открываем
                if self.messages.question(self, 'Новое сообщение',
                                          f'Получено новое сообщение от {sender}, открыть чат с ним?', QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                print('NO')
                # если нет, запрашиваем добавление в контакты
                if self.messages.question(self, 'Новое сообщение',
                                          f'Получено новое сообщение от {sender}.\n Данного пользователя нет в вашем контакт-листе.\n Добавить в контакты и открыть чат с ним?',
                                          QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.set_active_user()

    # слот потери соединения
    # выдает сообщение об ошибке и завершает приложение
    @pyqtSlot()
    def connection_lost(self):
        self.messages.warning(self, 'Сбой соединения, потеряно соединение')
        CLIENT_LOGGER.critical('Сбой соединения, потеряно соединение')
        self.close()

    def make_connection(self, transport_object):
        transport_object.new_message.connect(self.message)
        transport_object.connection_lost.connect(self.connection_lost)
