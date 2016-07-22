#!/usr/bin/env python
from setuptools import setup, find_packages
import pkg_resources
import sys
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

VERSION = '3.10'

install_requires = ['psutil', 'speedtest-cli']
extras_require={}
setup(name='Flora-Cli',
      version=VERSION,
      description="A basic commandline utility",
      long_description="A basic commandline utility developed by Fuzen-py",
      author='Fuzen.py',
      author_email='',
      url='https://github.com/Fuzen-py/Flora-Cli',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples',
                                      'tests', 'tests.*', 'release']),
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      extras_require=extras_require,
      scripts=['flora-cli']
      )
