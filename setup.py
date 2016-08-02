#!/usr/bin/env python
from setuptools import setup, find_packages
import pkg_resources
import sys
from os import name as dist_name, rename
from os.path import dirname, join, realpath
import os
try:
    if int(pkg_resources.get_distribution("pip").version.split('.')[0]) < 6:
        print('pip older than 6.0 not supported, please upgrade pip with:\n\n'
              '    pip install -U pip')
        sys.exit(-1)
except pkg_resources.DistributionNotFound:
    pass
version = sys.version_info[:2]
if version < (3, 5):
    print('Flora-Cli requires Python version 3.5 or later' +
          ' ({}.{} detected).'.format(*version))
    sys.exit(-1)

VERSION = '3.10a'
if os.name == 'nt':
    setup(name='Flora-Cli',
          version=VERSION,
          description="A basic commandline utility",
          long_description="A basic commandline utility developed by Fuzen-py",
          author='Fuzen.py',
          author_email='',
          url='https://github.com/Fuzen-py/Flora-Cli',
          license='MIT',
          packages=find_packages(exclude=['ez_setup', 'examples', 'tests', 'tests.*', 'release']),
          include_package_data=True,
          zip_safe=False,
          install_requires=['psutil', 'speedtest-cli', 'logbook'],
          extras_require={},
          scripts=['flora-cli.py'])
else:
    rename(join(dirname(realpath(__file__)), 'flora-cli.py'), join(dirname(realpath(__file__)), 'flora-cli'))
    setup(name='Flora-Cli',
          version=VERSION,
          description="A basic commandline utility",
          long_description="A basic commandline utility developed by Fuzen-py",
          author='Fuzen.py',
          author_email='',
          url='https://github.com/Fuzen-py/Flora-Cli',
          license='MIT',
          packages=find_packages(
              exclude=[
                  'ez_setup',
                  'examples',
                  'tests',
                  'tests.*',
                  'release'
                  ]
              ),
          include_package_data=True,
          zip_safe=False,
          install_requires=[
              'psutil',
              'speedtest-cli',
              'logbook'],
          extras_require={
              },
          scripts =['flora-cli'],
          entry_points={
              'console_scripts':[
                  'Flora-cli=flora-cli.core:main'
                  ]
              }
          )
    rename(join(dirname(realpath(__file__)), 'flora-cli'), join(dirname(realpath(__file__)), 'flora-cli.py'))
