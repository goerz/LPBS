#!/usr/bin/env python

from distutils.core import setup
import os

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='LPBS',
      version='0.9.0',
      description='Local Portable Batch System',
      author='Michael Goerz',
      author_email='goerz@physik.uni-kassel.de',
      url='https://github.com/goerz/LPBS',
      license='GPL',
      packages=['LPBS'],
      scripts=['lqsub', 'lqdel', 'lqstat'],
      long_description=read('README.rst'),
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Environment :: No Input/Output (Daemon)',
          'Intended Audience :: Science/Research',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Natural Language :: English',
          'Topic :: Scientific/Engineering',
          'Topic :: System :: Clustering'
      ]
     )
