# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages


PACKAGE_NAME = 'gitview'
PACKAGE_DESCRIPTION = ''


def read(filename):
    return open(filename, 'r').read().strip()


def get_install_requires():
    with open('requirements/base.txt', 'r') as f:
        return f.read().split(os.linesep)


setup(
    name=PACKAGE_NAME,
    version=read('VERSION.txt'),
    description=PACKAGE_DESCRIPTION,
    long_description=read('README.md'),
    author='Zhilong Yang',
    author_email='zyang@redhat.com',
    url='https://github.com/GitView/GitView',
    license='GPLv3',
    keywords='git statistics',

    install_requires=get_install_requires(),

    packages=find_packages(),
    include_package_data=True,
    exclude_package_data={'': ['viewapp/migrations/']},
)
