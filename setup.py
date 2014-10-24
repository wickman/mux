#!/usr/bin/env python
from setuptools import setup, find_packages, Command


__version__ = '0.1.0'


setup(
  name = 'mux',
  version = __version__,
  description = "python implementation of finagle's mux session protocol",
  url = 'http://github.com/wickman/mux',
  author = 'Brian Wickman',
  author_email = 'wickman@gmail.com',
  license = 'Apache License, Version 2.0',
  packages = find_packages(),
  zip_safe = True,
  classifiers          = [
    'Programming Language :: Python',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
  ],
)
