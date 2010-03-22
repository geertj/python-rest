#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from rest.mapper import Mapper


class TestMapper(object):

    def test_simple(self):
        mapper = Mapper()
        mapper.connect('/:a/:b')
        assert mapper.match('/foo/bar') == { 'a': 'foo', 'b': 'bar' }
        assert mapper.match('/foo/bar/baz') == None

    def test_method_aware(self):
        mapper = Mapper()
        mapper.connect('/:a/:b', method='GET')
        assert mapper.match('/foo/bar', method='GET') == \
                { 'a': 'foo', 'b': 'bar' }
        assert mapper.match('/foo/bar', method='POST') == None
        assert mapper.match('/foo/bar', method=None) == \
                { 'a': 'foo', 'b': 'bar' }

    def test_match_with_arguments(self):
        mapper = Mapper()
        mapper.connect('/:a/:b', key='value')
        assert mapper.match('/foo/bar') == \
                { 'a': 'foo', 'b': 'bar', 'key': 'value' }

    def test_alternative_format(self):
        mapper = Mapper()
        mapper.connect('/{a}/{b}')
        assert mapper.match('/foo/bar') == { 'a': 'foo', 'b': 'bar' }

    def test_url_for(self):
        mapper = Mapper()
        mapper.connect('/:a/:b', action='test')
        assert mapper.url_for(action='test', a='foo', b='bar') == '/foo/bar'
        assert mapper.url_for(action='tst', a='foo', b='bar') == None
        assert mapper.url_for(action='test', a='foo', b='bar', c='baz') == None

    def test_methods_for(self):
        mapper = Mapper()
        mapper.connect('/:a/:b', action='test', method='GET')
        assert mapper.methods_for('/foo/bar') == ['GET']
        mapper.connect('/:a/:b', action='test', method='POST')
        assert mapper.methods_for('/foo/bar') == ['GET', 'POST']
