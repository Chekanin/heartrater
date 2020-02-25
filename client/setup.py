#!/usr/bin/env python3

from glob import glob
from setuptools import setup

setup(
    name='heartrater_client',
    version='0.0.1',
    url='https://github.com/Chekanin/heartrater',
    author='Anton Chekanin',
    author_email='antonchekanin@gmail.com',
    packages=[
        'miband',
    ],
    package_dir={'': 'src'},
    scripts=['bin/heartrater_client'],
    install_requires=open('./requirements.txt').read(),
    data_files=[
        ('/usr/lib/systemd/system', [
            'systemd/heartrater_client.service'
        ]),
        ('/etc/heartrater', glob('conf/*'))
    ]
)
