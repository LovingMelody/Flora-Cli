#!/usr/bin/env python
from setuptools import setup

setup(
    name='Flora-Cli',
    version='1.0.4',
    packages=['FloraCli'],
    url='https://github.com/Fuzen-py/Flora-cli',
    license='MIT',
    author='Fuzen.py',
    author_email='',
    description='Python 3 Command Line',
    long_description='A Python3 command line utility that is currently not stable',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Linux',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Scripts'
    ],
    keywords="Commandline update",
    install_requires=['psutil', 'logbook', 'speedtest-cli'],
    entry_points={
        'console_scripts': [
            'flora-cli=FloraCli:main'
        ]
    })
