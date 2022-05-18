"""
1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
(«Узел доступен», «Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
"""

from subprocess import Popen, PIPE
from ipaddress import ip_address


def host_ping(ip, timeout=1000, requests=1):
    result = {'Узел доступен':'', 'Узел недоступен':''}
    for adress in ip:
        try:
            adress = ip_address(adress)
        except ValueError: #обход ошибки Value error
            pass
        walk = Popen(f'ping {adress} -w {timeout} -n {requests}', shell=False, stdout=PIPE)
        walk.wait()
        if walk.returncode == 0:
            result['Узел доступен'] += f'{str(adress)}, '
        else:
            result['Узел недоступен'] += f'{str(adress)}, '
    for key, value in result.items():
        print(f'{key}: {value}')
    return result

ip_list = ['yandex.ru', 'google.ru', 'facebook.com', 'instagram.com']
host_ping(ip_list)

"""
результаты:
Узел доступен: yandex.ru, google.ru, facebook.com, 
Узел недоступен: instagram.com, 
"""