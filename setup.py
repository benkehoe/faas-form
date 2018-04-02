#!/usr/bin/env python

import os.path
from setuptools import setup

def get_version(name):
    import os.path
    path = os.path.join(name, '_version')
    if not os.path.exists(path):
        return "0.0.0"
    with open(path) as f:
        return f.read().strip()

requires = [
    'boto3>=1.2.0',
    'setuptools>=20.6.6',
    'six>=1.0.0',
]

setup(
    name='faas-form',
    version=get_version('faas_form'),
    description='',
    author='Ben Kehoe',
    author_email='bkehoe@irobot.com',
    url='https://github.com/iRobotCorporation/faas-form',
    packages=["faas_form"],
    package_data={
        "faas_form": ["_version"]
    },
    entry_points={
        'console_scripts': [
            'faas-form = faas_form.cli:main',
        ],
    },
    install_requires=requires,
    classifiers=(
        'Development Status :: 2 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ),
)
