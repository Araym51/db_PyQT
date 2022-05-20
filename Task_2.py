"""
2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
Меняться должен только последний октет каждого адреса.
По результатам проверки должно выводиться соответствующее сообщение.
"""

from ipaddress import ip_address
from Task_1 import host_ping

def host_range_ping():
    while True:
        start = input('Введите адрес с которого начать: ')
        try:
            last_octet = int(start.split('.')[3])
            break
        except Exception as error:
            print(error)
    while True:
        quantity = input('Сколько адресов проверяем?: ')
        if not quantity.isnumeric():
            print('Введите число: ')
        else:
            if (last_octet + int(quantity)) > 254:
                print(f'так как изменяем только последний октет, максимальное число для проверки: {254 - quantity}')
            else:
                break

    hosts = []
    [hosts.append(str(ip_address(start) + x)) for x in range(int(quantity))]
    return host_ping(hosts)

if __name__ == '__main__':
    host_range_ping()

"""
результат:
Введите адрес с которого начать: 192.168.100.1
Сколько адресов проверяем?: 20
Узел доступен: 192.168.100.1, 192.168.100.4, 192.168.100.6, 192.168.100.7, 192.168.100.8, 192.168.100.13, 
Узел недоступен: 192.168.100.2, 192.168.100.3, 192.168.100.5, 192.168.100.9, 192.168.100.10, 192.168.100.11, 
192.168.100.12, 192.168.100.14, 192.168.100.15, 192.168.100.16, 192.168.100.17, 192.168.100.18, 192.168.100.19, 
192.168.100.20, 
"""