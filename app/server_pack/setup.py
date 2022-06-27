from setuptools import setup, find_packages

setup(
    name='messenger',
    version='0.0.1',
    description='messenger_server_project',
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