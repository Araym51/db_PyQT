from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import datetime


# класс база клиента
class ClientDatabase:
    # отображение известных пользователей
    class KnownUsers:
        def __init__(self, user):
            self.id = None
            self.username = user

    # история сообщений
    class MessageHistory:
        def __init__(self, contact, direction, message):
            self.id = None
            self.contact = contact
            self.direction = direction
            self.message = message
            self.date = datetime.datetime.now()

    # список контактов
    class Contacts:
        def __init__(self, contact):
            self.id = None
            self.name = contact

    def __init__(self, name):
        # создаем движок БД, поскольку разрешено несколько клинтов одновременно, каждый должен иметь свою БД.
        # отключаем проверку на подключение с разных потоков для избежание sqlite.ProgrammingError
        self.database_engine = create_engine(f'sqlite:///client_{name}.db3', echo=False, pool_recycle=7200,
                                             connect_args={'check_same_thread': False})

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

        # создаем отображения
        mapper(self.KnownUsers, users)
        mapper(self.MessageHistory, history)
        mapper(self.Contacts, contacts)

        # создаем сессию
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # очищаем список контактов
        self.session.query(self.Contacts).delete()
        self.session.commit()

    # функуция добавления контактов
    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    # удаление котакта:
    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()

    # функция добавляет известных пользователей.
    def add_users(self, users_list):
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    # функция для сохранения сообщений
    def save_message(self, contact, direction, message):
        message_row = self.MessageHistory(contact, direction, message)
        self.session.add(message_row)
        self.session.commit()

    # фунция запроса котактов
    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    # функция запроса пользователей
    def get_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    # функция проверяющая наличие пользователя в списке известных
    def check_user(self, user):
        if self.session.query(self.KnownUsers).filter_by(username=user).count():
            return True
        else:
            return False

    # проверка наличия пользователя в контактах
    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    # функция возвращающая историю переписки
    def get_history(self, contact):
        query = self.session.query(self.MessageHistory).filter_by(contact=contact)
        return [(history_row.contact, history_row.direction, history_row.message, history_row.date)
                for history_row in query.all()]


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
