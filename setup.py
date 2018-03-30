#!/usr/bin/env python3

import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='ligatures',
    version='1.0.0',
    author='Adam Heins',
    author_email='mail@adamheins.com',
    description='Ligature manipulation and inference.',
    license='MIT',
    keywords='ligature',
    url='https://github.com/adamheins/ligatures',
    packages=['ligatures'],
    long_description=read('README.md'),
)
