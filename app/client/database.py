from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import datetime
import os


class ClientDatabase:
    '''
    Класс для работы с БД клиента.
    '''
    class KnownUsers:
        '''
        Класс - отображение известных пользователей
        '''
        def __init__(self, user):
            self.id = None
            self.username = user

    class MessageStat:
        '''
        Класс - история сообщений.
        '''
        def __init__(self, contact, direction, message):
            self.id = None
            self.contact = contact
            self.direction = direction
            self.message = message
            self.date = datetime.datetime.now()

    class Contacts:
        '''
        Класс - список контактов.
        '''
        def __init__(self, contact):
            self.id = None
            self.name = contact

    # Конструктор класса:
    def __init__(self, name):
        # создаем движок БД, поскольку разрешено несколько клинтов одновременно, каждый должен иметь свою БД.
        # отключаем проверку на подключение с разных потоков для избежание sqlite.ProgrammingError
        path = os.path.dirname(os.path.realpath(__file__))
        filename = f'client_{name}.db3'
        self.database_engine = create_engine(
            f'sqlite:///{os.path.join(path, filename)}',
            echo=False,
            pool_recycle=7200,
            connect_args={
                'check_same_thread': False})

        self.metadata = MetaData()

        # таблица известных пользователей.
        users = Table('known_users', self.metadata,
                      Column('id', Integer, primary_key=True),
                      Column('username', String)
                      )

        # история сообщений
        history = Table('message_history', self.metadata,
                        Column('id', Integer, primary_key=True),
                        Column('contact', String),
                        Column('direction', String),
                        Column('message', Text),
                        Column('date', DateTime)
                        )

        # таблица с контактами
        contacts = Table('contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('name', String, unique=True)
                         )

        # создаем таблицы
        self.metadata.create_all(self.database_engine)

        # создаём отображения
        mapper(self.KnownUsers, users)
        mapper(self.MessageStat, history)
        mapper(self.Contacts, contacts)

        # создаём сессию
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # очищаем список контактов
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        '''функуция добавления контактов'''
        if not self.session.query(
                self.Contacts).filter_by(
                name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def contacts_clear(self):
        '''удаление списка котактов'''
        self.session.query(self.Contacts).delete()

    def del_contact(self, contact):
        '''удаление определенного котакта.'''
        self.session.query(self.Contacts).filter_by(name=contact).delete()

    def add_users(self, users_list):
        '''функция добавляет известных пользователей.'''
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, contact, direction, message):
        '''функция для сохранения сообщений.'''
        message_row = self.MessageStat(contact, direction, message)
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        '''фунция запроса котактов.'''
        return [contact[0]
                for contact in self.session.query(self.Contacts.name).all()]

    def get_users(self):
        '''функция запроса пользователей.'''
        return [user[0]
                for user in self.session.query(self.KnownUsers.username).all()]

    def check_user(self, user):
        '''функция проверяющая наличие пользователя в списке известных.'''
        if self.session.query(
                self.KnownUsers).filter_by(
                username=user).count():
            return True
        else:
            return False

    def check_contact(self, contact):
        '''проверка наличия пользователя в контактах.'''
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    def get_history(self, contact):
        '''функция возвращающая историю переписки.'''
        query = self.session.query(
            self.MessageStat).filter_by(
            contact=contact)
        return [(history_row.contact,
                 history_row.direction,
                 history_row.message,
                 history_row.date) for history_row in query.all()]


# отладка
if __name__ == '__main__':
    test_db = ClientDatabase('a_chan')
    # for i in ['2_chan', '3_chan', '4_chan']:
    #     test_db.add_contact(i)
    # test_db.add_contact('5_chan')
    # test_db.add_users(['1_chan', '2_chan', '3_chan', '4_chan', '5_chan'])
    # test_db.save_message('1_chan', '2_chan', f'Привет! проверка связи! Время проверки: {datetime.datetime.now()}!')
    # test_db.save_message('2_chan', '1_chan', f'Привет! Тоже проверка связи! Время проверки: {datetime.datetime.now()}!')
    # print(test_db.get_contacts())
    # print(test_db.get_users())
    # print(test_db.check_user('1_chan'))
    # print(test_db.check_user('10_chan'))
    # print(test_db.get_history('2_chan'))
    # print(test_db.get_history(to_who='2_chan'))
    # print(test_db.get_history('1_chan'))
    # test_db.del_contact('4_chan')
    # print(test_db.get_contacts())
