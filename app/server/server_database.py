from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import datetime
import sys
sys.path.append('../')
from common.constants import *


# класс для серверной базы данных
class ServerStorage:
    """
    Класс оболочка для работы с БД сервера.
    Использует SQLite БД.
    Реализован с помощью SQLAlchemy ORM и использует классический подход.
    """
    class AllUsers:
        """
        класс табилца для отображения всех пользователей
        """
        def __init__(self, username, passwd_hash):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.passwd_hash = passwd_hash
            self.pubkey = None
            self.id = None

    class ActiveUsers:
        """
        Отображение активных пользователейЭкземпляр - запись в таблице ActiveUsers
        """
        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    class LoginHistory:
        """
        Отображение истории посещений. Экземпля - запись в таблице LoginHistory
        """
        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

    class UsersContacts:
        """
        Контакты пользователей
        """
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    class UsersHistory:
        """
        Класс отображения таблицы истории действий
        """
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        # создаем движок БД (константа SERVER_DATABASE)
        # echo=False - отключает ведение логов (вывод sql-запросов)
        # pool_recycle - через 2 часа переустановка соединения
        print(path)
        self.database_engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200,
                                             connect_args={'check_same_thread': False})
        # Создаем объект MetaData
        self.metadata = MetaData()

        # Таблица с пользователями
        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime)
                            )

        # таблица с активными пользователями
        active_users_table = Table('Active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id'), unique=True),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime)
                                   )

        # таблица истории посещений пользователей
        user_login_history = Table('Login_history', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('name', ForeignKey('Users.id')),
                                   Column('date_time', DateTime),
                                   Column('ip', String),
                                   Column('port', String)
                                   )

        # таблица с контактами пользователей
        contacts = Table('Contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('user', ForeignKey('Users.id')),
                         Column('contact', ForeignKey('Users.id'))
                         )

        # таблица истории пользователей
        users_history_table = Table('History', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user', ForeignKey('Users.id')),
                                    Column('sent', Integer),
                                    Column('accepted', Integer)
                                    )
        # создаем описанные выше таблицы
        self.metadata.create_all(self.database_engine)
        # отображения:
        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, user_login_history)
        mapper(self.UsersContacts, contacts)
        mapper(self.UsersHistory, users_history_table)

        # создаем сессию
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # удаляем записи при наличии. Устанавливая соедниение, очищаем от активных пользователей
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    # функция записывает факт входа пользователя
    def user_login(self, username, ip_address, port, key):
        """
        Метод выполняется при входе пользователя. Записывает в базу факт входа
        обновляет открытый ключ пользователя при его изменении.
        """
        print(username, ip_address, port)
        # запрос в таблицу пользователей, на наличие там поьзователя с таким именем
        result = self.session.query(self.AllUsers).filter_by(name=username)
        # Если такой пользователь уже есть, обновляем дату последнего входа
        if result.count():
            user = result.first()
            user.last_login = datetime.datetime.now()
            if user.pubkey != key:
                user.pubkey = key
        # Если нет, создаем нового пользователя
        else:
            # создаем экземпляр AllUsers, через который записываем данные в таблицу
            raise ValueError('Пользователь не зарегистрирован')

        # записываем факт входа в таблицу активных пользователей черезы ActiveUsers
        new_active_user = self.ActiveUsers(user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)

        # сохраняем историю входов в LoginHistory
        history = self.LoginHistory(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(history)

        # Сохраняем изменения
        self.session.commit()

    def add_user(self, name, password_hash):
        """
        метод регистрации пользователя.
        принимает имя и хэш пароля, создает запись в таблице статистики
        """
        user_row = self.AllUsers(name, password_hash)
        self.session.add(user_row)
        self.session.commit()
        history_row = self.UsersHistory(user_row.id)
        self.session.add(history_row)
        self.session.commit()

    def remove_user(self, name):
        '''Метод удаляющий пользователя из базы.'''
        user = self.session.query(self.AllUsers).filter_by(name=name).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.query(self.LoginHistory).filter_by(name=user.id).delete()
        self.session.query(self.UsersContacts).filter_by(user=user.id).delete()
        self.session.query(
            self.UsersContacts).filter_by(
            contact=user.id).delete()
        self.session.query(self.UsersHistory).filter_by(user=user.id).delete()
        self.session.query(self.AllUsers).filter_by(name=name).delete()
        self.session.commit()

    def get_hash(self, name):
        '''Метод получения хэша пароля пользователя.'''
        user = self.session.query(self.AllUsers).filter_by(name=name).first()
        return user.passwd_hash

    def get_pubkey(self, name):
        '''Метод получения публичного ключа пользователя.'''
        user = self.session.query(self.AllUsers).filter_by(name=name).first()
        return user.pubkey

    def check_user(self, name):
        '''Метод проверяющий существование пользователя.'''
        if self.session.query(self.AllUsers).filter_by(name=name).count():
            return True
        else:
            return False

    # Функция фиксирует отключение пользователя
    def user_logout(self, username):
        # Запрос отключаемого пользователя из таблицы AllUsers
        user = self.session.query(self.AllUsers).filter_by(name=username).first()

        # Удаляем его из таблицы активных пользователей ActiveUsers
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()

        # Применяем изменения
        self.session.commit()

    def process_message(self, sender, recipient):
        """
        Функция записывает факт сообщения в БД
        """
        sender = self.session.query(self.AllUsers).filter_by(name=sender).first().id
        recipient = self.session.query(self.AllUsers).filter_by(name=recipient).first().id
        sender_row = self.session.query(self.UsersHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1
        self.session.commit()

    # добавление контакта для пользователя
    def add_contact(self, user, contact):
        """
        Добавление контакта для пользователя
        """
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()

        # проверка что не дубль
        if not contact or self.session.query(self.UsersContacts).filter_by(user=user.id, contact=contact.id).count():
            return
        # создаем и добавляем объект в базу
        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def remove_contact(self, user, contact):
        """
        удаление контакта
        """
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()

        # проверяем существования контакта
        if not contact:
            return

        # удаляем ненужное
        self.session.query(self.UsersContacts).filter(self.UsersContacts.user == user.id,
                                                      self.UsersContacts.contact == contact.id).delete()
        self.session.commit()

    # Функция возвращает список известных пользователей, со временм последнего входа
    def users_list(self):
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
        )
        return query.all()

    def active_users_list(self):
        """ Функция возвращает список активных пользователей"""
        # запрашиваем список таблиц и собираем имя, ip, порт, время
        query = self.session.query(
            self.AllUsers.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)
        return query.all()

    def login_history(self, username=None):
        """
        Метод возвращает историю входов
        """
        query = self.session.query(
            self.AllUsers.name,
            self.LoginHistory.date_time,
            self.LoginHistory.ip,
        ).join(self.AllUsers)

        if username:
            query = query.filter(self.AllUsers.name == username)
        return query.all()

    def get_contacts(self, username):
        """
        получение списка контактов пользователя
        """
        user = self.session.query(self.AllUsers).filter_by(name=username).one()
        query = self.session.query(self.UsersContacts, self.AllUsers.name).filter_by(user=user.id).join(self.AllUsers,
                                                                                                        self.UsersContacts.contact == self.AllUsers.id)
        # получаем только имена
        return [contact[1] for contact in query.all()]

    def message_history(self):
        """
        получает количество переданных и полученных сообщений
        """
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.AllUsers)
        return query.all()


if __name__ == '__main__':
    testing = ServerStorage()
    testing.user_login('user', '192.168.1.1', 8888)
    testing.user_login('user_2', '192.168.1.2', 8887)
    print(testing.active_users_list())
    testing.user_logout('user')
    print(testing.active_users_list())
    testing.login_history()
    print(testing.users_list())
    testing.process_message('Aaaa', 'Bbbb')
    print(testing.message_history())
