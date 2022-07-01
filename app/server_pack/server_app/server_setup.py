import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    'packages': ['common', 'loging', 'server', 'sqlalchemy'],
}

setup(
    name='mess_client',
    version='0.0.1',
    description='mess_server',
    options={
        'build_exe': build_exe_options
    },
    executables=[Executable('server_app_.py',
                            base='Win32GUI',
                            targetName='server.exe')]
)

# python .\server_setup.py build_exe