#!/usr/bin/env python3

from glob import glob
from setuptools import setup
import os


setup(
    name='heartrater_server',
    version='0.0.1',
    url='https://github.com/Chekanin/heartrater',
    author='Anton Chekanin',
    author_email='antonchekanin@gmail.com',
    #  package_dir={'': 'src'},
    scripts=['bin/heartrater_server'],
    install_requires=open('./requirements.txt').read(),
    data_files=[
        ('/usr/lib/systemd/system', [
            'systemd/heartrater_server.service'
        ]),
        ('/usr/share/heartrater/static', glob('static/*')),
        ('/etc/heartrater', glob('conf/*'))
    ]
)

LOGS_DIR = '/var/log/heartrater'
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)
