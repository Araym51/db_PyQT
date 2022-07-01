import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    'packages': ['common', 'loging', 'client', 'sqlalchemy'],
}

setup(
    name='mess_client',
    version='0.0.1',
    description='mess_client',
    options={
        'build_exe': build_exe_options
    },
    executables=[Executable('client_app.py',
                            base='Win32GUI',
                            targetName='cleint.exe')]
)

# python .\client_setup.py build_exe
