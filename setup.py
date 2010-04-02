#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from setuptools import setup

setup(
    name = 'python-rest',
    version = '1.1',
    description = 'A mini-framework for creating RESTful applications.',
    author = 'Geert Jansen',
    author_email = 'geertj@gmail.com',
    url = 'http://bitbucket.org/geertj/python-rest',
    license = 'MIT',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'],
    package_dir = {'': 'lib'},
    packages = ['rest', 'rest.test'],
    test_suite = 'nose.collector'
)
