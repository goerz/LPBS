#!/usr/bin/env python

from distutils.core import setup

setup(name='lpbs',
      version='1.0dev',
      description='Local Portable Batch System',
      author='Michael Goerz',
      author_email='goerz@physik.uni-kassel.de',
      url='https://github.com/goerz/LPBS',
      license='GPL',
      packages=['LPBS'],
      scripts=['lqsub', 'lqdel', 'lqstat']
     )
