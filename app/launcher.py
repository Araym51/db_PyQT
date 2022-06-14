import subprocess

PROCESS = []

while True:
    COMMANDS = input('Доступные команды: q - выход из приложения, '
                     's - запустить сервер и клиенты, x - закрыть все окна: ')

    if COMMANDS == 'q':
        break
    elif COMMANDS == 'S':
        PROCESS.append(subprocess.Popen('python server_app.py',
                                        creationflags=subprocess.CREATE_NEW_CONSOLE))

        for i in range(2):
            PROCESS.append(
                subprocess.Popen('python client_app.py -m send',
                                 creationflags=subprocess.CREATE_NEW_CONSOLE))

        for j in range(5):
            PROCESS.append(
                subprocess.Popen('python client_app.py -m listen',
                                 creationflags=subprocess.CREATE_NEW_CONSOLE))

    elif COMMANDS == 'x':
        while PROCESS:
            victim = PROCESS.pop()
            victim.kill()
