import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, QTableView, QDialog, QPushButton, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
import os

def gui_create_model(database):
    users_list = database.active_users_list()
    list_ = QStandardItemModel()
    list_.setHorizontalHeaderLabels(['Имя клиента', 'IP-адрес', "Порт", "Время подключения"])
    for row in users_list:
        user, ip, port, time = row
        user = QStandardItem(user)
        user.setEditable(False) # запрет изменения
        ip = QStandardItem(ip)
        ip.setEditable(False)
        port = QStandardItem(port)
        port.setEditable(False)
        time = QStandardItem(str(time.replace(microsecond=0)))
        time.setEditable(False)
        list_.appendRow([user, ip, port, time])  #добавляем строку
    return list_

def create_stat_model(database):
    history = database.message_history

    list_ = QStandardItemModel()
    list_.setHorizontalHeaderLabels(['Имя Клиента', 'Последний раз входил', 'Сообщений отправлено', 'Сообщений получено'])

    for row in history:
        user, last_seen, sent_message, recieved_message = row
        user = QStandardItem(user)
        user.setEditable(False)
        last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
        last_seen.setEditable(False)
        sent_message = QStandardItem(sent_message)
        sent_message.setEditable(False)
        recieved_message = QStandardItem(recieved_message)
        recieved_message.setEditable(False)
        list_.appendRow([user, last_seen, sent_message, recieved_message])
    return list_


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def iniyUI(self):
        exitAction = QAction('Выход', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(qApp.quit)
        # обновление списка клиентов
        self.refresh_button = QAction('Обновить список', self)
        # настройки сервера
        self.server_config = QAction("Настройки", self)
        # история сообщений
        self.show_history_button = QAction("История клиентов", self)
        # статусбар
        self.statusBar()

        # ПАНЕЛЬ ИНСТРУМЕНТОВ
        self.toolbar = self.addToolBar('Паенль инструментов')
        self.toolbar.addAction(exitAction)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.server_config)

        # окно с подключенными клиентами
        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 45)
        self.active_clients_table.setFixedSize(780, 400)

        # Последним параметром отображаем окно.
        self.show()


class HistoryMainWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Статистика клиентов")
        self.setFixedSize(800, 600)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.close_button = QPushButton('Закрыть окно', self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(580,620)

        self.show()


class ConfigWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setFixedSize(365, 260)
        self.setWindowTitle('Настройки сервера')

        self.db_path_label = QLabel('путь до файла базы данных: ', self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(240, 15)

        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(250, 20)
        self.move(10, 30)
        self.db_path.setReadOnly(True)

        self.db_path_select = QPushButton('Обзор', self)
        self.db_path_select.move(275, 28)

        def open_file_dialog():
            global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.insert(path)

        # метка с именем поля файла БД
        self.db_path_select.clicked.connect(open_file_dialog)
        self.db_file_label = QLabel('Имя файла базы данных', self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(180, 15)

        # поле ввода имени БД
        self.db_file = QLineEdit(self)
        self.db_file.move(200, 66)
        self.db_file.setFixedSize(150, 20)

        # метка с номером порта
        self.port = QLineEdit(self)
        self.port.move(10, 108)
        self.port.setFixedSize(150, 20)

        # поле ввода ip-адреса
        self.ip = QLineEdit(self)
        self.ip.move(200, 148)
        self.ip.setFixedSize(150, 20)

        # Метка с адресом для соединений
        self.ip_label = QLabel('С какого IP принимаем соединения:', self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(180, 15)

        # Метка с напоминанием о пустом поле.
        self.ip_label_note = QLabel(' оставьте это поле пустым, чтобы\n принимать соединения с любых адресов.', self)
        self.ip_label_note.move(10, 168)
        self.ip_label_note.setFixedSize(500, 30)

        # кнопка сохранения настроек
        self.save_button = QPushButton("Применить",self)
        self.save_button.move(190, 220)

        # кнопка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(10, 148)
        self.close_button.clicked.connect(self.close)

        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.statusBar().showMessage('Test Statusbar Message')
    test_list = QStandardItemModel(ex)
    test_list.setHorizontalHeaderLabels(['Имя Клиента', 'IP Адрес', 'Порт', 'Время подключения'])
    test_list.appendRow([QStandardItem('1'), QStandardItem('2'), QStandardItem('3')])
    test_list.appendRow([QStandardItem('4'), QStandardItem('5'), QStandardItem('6')])
    ex.active_clients_table.setModel(test_list)
    ex.active_clients_table.resizeColumnsToContents()
    print('JKJKJK')
    app.exec_()
    print('END')
