from setuptools import find_packages, setup

setup(
    name='pymyelarepl',
    version='0.2',
    packages=find_packages(
        include=[
            'pymyelarepl'
        ]),
    install_requires = [
        'certifi==2023.7.22',
        'cffi==1.15.1',
        'charset-normalizer==3.2.0',
        'cryptography==41.0.4',
        'idna==3.4',
        'mysql-replication==0.43.0',
        'pycparser==2.21',
        'PyMySQL==1.1.0',
        'PyYAML==6.0.1',
        'requests==2.31.0',
        'urllib3==2.0.4'       
    ]
)