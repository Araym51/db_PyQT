import dis

# метакласс для контроля поведения серверной части:
class ServerMarker(type):
    def __init__(self, clsname, bases, cldict):
        """
        :param clsname: экземпляр метакласса Server
        :param bases: кортеж базовых классов
        :param cldict: словарь атрибутов и методов экземпляра метакласса
        """
        # методы используемые в функциях класса
        methods = []
        # атрибуты в функциях классов
        attrs = []
        # перебираем ключи:
        for func in cldict:
            try:
                # Возвращает итератор по инструкциям в представленной функции,
                # методе, строке исходного кода или объекта кода
                ret = dis.get_instructions(cldict[func])
            # Если не функуия, ловим исключение
            except TypeError:
                pass
            else:
                for i in ret:
                    print(i)
                    # i - инструкция
                    # opname - имя операции
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            # заполняем список методами, использующимися в функциях класса
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            # заполняем список атрибутами, использующимися в функциях класса
                            attrs.append(i.argval)
        print(methods)
        # при обнаружении connect бросаем исключение:
        if 'connect' in methods:
            raise TypeError('Метод "connect" нельзя использовать в серверном классе')
        # При отсутствии 'SOCK_STREAM' 'AF_INET', бросаем исключение:
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета')
        # вызываем конструктор предка
        super().__init__(clsname, bases, cldict)


# метакласс для контроля поведения клиентской части:
class ClientMarker(type):
    def __init__(self, clsname, bases, clsdict):
        # список методов в функциях класса
        methods = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            # если не функция - бросаем исключение:
            except TypeError:
                pass
            else:
                # если все хорошо - разбираем код, получаем методы
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
        for command in ('accept', 'listen', 'sockets'):
            if command in methods:
                raise TypeError('В классе обнаружено использование запрещенного метода')
        # Использование recieve_message() и send_message() мсчитаем корректным использованием сокетов
        if 'send_message' in methods or 'recieve_message' in methods:
            pass
        else:
            raise TypeError('Отсутствуют вызовы функций, работающих с сокетами')
        # вызываем конструктор предка
        super().__init__(clsname, bases, clsdict)