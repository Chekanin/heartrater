from setuptools import setup, find_packages

setup(
    name="heartrater_server",
    author="Anton Chekanin",
    author_email="antonchekanin@gmail.com",
    packages=find_packages(),
    install_requires=open('./requirements.txt').read(),
    dependency_links=[
        'https://pypi.yandex-team.ru/simple/',
    ],
)
