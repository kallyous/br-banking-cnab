#!/usr/bin/env python

from distutils.core import setup

setup(
    name='br-banking-cnab',
    version='0.2.0-dev.1',
    packages=['brbankingcnab'],
    package_data={'brbankingcnab': ['brbankingcnab/templates/*']},
    url='https://github.com/kallyous/br-banking-cnab',
    description='Package for easy creating and handling Brazilian banking CNAB files.',
    license='MIT License'
)
