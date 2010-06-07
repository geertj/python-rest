#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import sys
import os.path
import inspect

from distutils.command.build import build
from setuptools import setup


version_info = {
    'name': 'python-rest',
    'version': '1.2',
    'description': 'A mini-framework for creating RESTful applications.',
    'author': 'Geert Jansen',
    'author_email': 'geertj@gmail.com',
    'url': 'http://bitbucket.org/geertj/python-rest',
    'license': 'MIT',
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application' ]
}


class mybuild(build):

    def _topdir(self):
        fname = inspect.getfile(sys.modules['__main__'])
        absname = os.path.abspath(fname)
        return os.path.split(absname)[0]

    def _store_version(self):
        fname = os.path.join(self._topdir(), 'lib', 'rest', '_version.py')
        contents = '# This is a geneated file - do not edit!\n'
        version = tuple(map(int, version_info['version'].split('.')))
        contents += 'version = %s\n' % repr(version)
        try:
            fin = file(fname, 'r')
        except IOError:
            current = None
        else:
            current = fin.read()
            fin.close()
        if contents != current:
            fout = file(fname, 'w')
            fout.write(contents)
            fout.close()

    def run(self):
        self._store_version()
        build.run(self)


setup(
    package_dir = {'': 'lib'},
    packages = ['rest', 'rest.test'],
    test_suite = 'nose.collector',
    entry_points = { 'console_scripts': [
            'python-rest-cmdline = rest.server:main' ] },
    install_requires = ['argproc >= 1.2'],
    cmdclass = { 'build': mybuild },
    **version_info
)
