from setuptools import setup, find_packages

setup(
    name='client_pyqt_chat_June_Araym51',
    version='0.0.1',
    description='messenger_client_project',
    author='Egor Ostroumov',
    author_email='araimo@yandex.ru',
    packages=find_packages(),
    install_requires=[
        'pycryptodome',
        'PyQt5',
        'sqlalchemy',
        'pycryptodomex'
    ]
)