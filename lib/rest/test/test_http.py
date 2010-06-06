#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from rest.http import *
from nose.tools import assert_raises


class TestParseListHeader(object):

    def test_simple(self):
        header = 'text/html'
        parsed = [('text/html', [])]
        assert parse_list_header(header) == parsed

    def test_parameter(self):
        header = 'text/html; charset=utf8'
        parsed = [('text/html', [('charset', 'utf8')])]
        assert parse_list_header(header) == parsed

    def test_multiple_parameters(self):
        header = 'text/html; charset=utf8; level=1'
        parsed = [('text/html', [('charset', 'utf8'), ('level', '1')])]
        assert parse_list_header(header) == parsed

    def test_multiple_headers(self):
        header = 'text/html, text/plain'
        parsed = [('text/html', []), ('text/plain', [])]
        assert parse_list_header(header) == parsed

    def test_multiple_headers_multiple_parameters(self):
        header = 'text/html; charset=utf8; level=1,' \
                 ' text/plain; charset=us-ascii; level=2'
        parsed = [('text/html', [('charset', 'utf8'), ('level', '1')]),
                  ('text/plain', [('charset', 'us-ascii'), ('level', '2')])]
        assert parse_list_header(header) == parsed

    def test_quoted_parameter(self):
        header = 'text/html; charset="utf 8"'
        parsed = [('text/html', [('charset', 'utf 8')])]
        assert parse_list_header(header) == parsed

    def test_quoted_parameter_with_escape(self):
        header = r'text/html; charset="utf\"8"'
        parsed = [('text/html', [('charset', 'utf"8')])]
        assert parse_list_header(header) == parsed

    def test_split_content_type(self):
        header = 'text/html; charset=utf8'
        parsed = [('text', 'html', [('charset', 'utf8')])]
        assert parse_list_header(header, split_content_type=True) == parsed

    def test_lower_case(self):
        header = 'Text/Html; Charset=Utf8'
        parsed = [('text/html', [('charset', 'Utf8')])]
        assert parse_list_header(header, lower_case=True) == parsed

    def test_options_as_dict(self):
        header = 'text/html; charset=utf8'
        parsed = [('text/html', {'charset': 'utf8'})]
        assert parse_list_header(header, options_as_dict=True) == parsed

    def test_error_missing_quote(self):
        header = 'text/html; charset="utf8'
        assert_raises(ValueError, parse_list_header, header)

    def test_error_missing_parameter(self):
        header = 'text/html; =utf8'
        assert_raises(ValueError, parse_list_header, header)

    def test_error_missing_value(self):
        header = 'text/html; charset='
        assert_raises(ValueError, parse_list_header, header)


class TestParseContentType(object):

    def test_simple(self):
        ctype = 'text/html'
        parsed = ('text', 'html', {})
        assert parse_content_type(ctype) == parsed

    def test_options(self):
        ctype = 'text/html; charset=utf8'
        parsed = ('text', 'html', {'charset': 'utf8'})
        assert parse_content_type(ctype) == parsed

    def test_multiple_options(self):
        ctype = 'text/html; charset=utf8; foo=bar'
        parsed = ('text', 'html', {'charset': 'utf8', 'foo': 'bar'})
        assert parse_content_type(ctype) == parsed


class TestSelectContentType(object):

    def test_simple(self):
        accept = 'text/html, text/plain'
        ctypes = ('text/html', 'text/plain')
        assert select_content_type(ctypes, accept) == ctypes[0]

    def test_quality_factor(self):
        accept = 'text/html; q=0.8, text/plain; q=0.9'
        ctypes = ('text/html', 'text/plain')
        assert select_content_type(ctypes, accept) == ctypes[1]

    def test_default_quality_factor(self):
        accept = 'text/html, text/plain; q=0.9'
        ctypes = ('text/html', 'text/plain')
        assert select_content_type(ctypes, accept) == ctypes[0]

    def test_specificity(self):
        accept = 'text/xml; q=0.7, text/*; q=0.9, text/plain; q=0.8'
        ctypes = ('text/xml', 'text/plain')
        assert select_content_type(ctypes, accept) == ctypes[1]
        accept = 'text/xml; level=1; q=0.7, text/xml; q=0.9, text/plain; q=0.8'
        ctypes = ('text/xml; level=1', 'text/plain')
        assert select_content_type(ctypes, accept) == ctypes[1]

    def test_non_matching(self):
        accept = 'text/html, text/plain'
        ctypes = ('text/xml', 'application/xml')
        assert select_content_type(ctypes, accept) is None


class TestSelectCharset(object):

    def test_simple(self):
        accept = 'utf-8'
        charsets = ('utf-8', 'utf-16')
        assert select_charset(charsets, accept) == charsets[0]

    def test_quality_factor(self):
        accept = 'utf-8; q=0.8, utf-16; q=0.9'
        charsets = ('utf-8', 'utf-16')
        assert select_charset(charsets, accept) == charsets[1]

    def test_default_quality_factor(self):
        accept = 'utf-8, utf-16; q=0.9'
        charsets = ('utf-8', 'utf-16')
        assert select_charset(charsets, accept) == charsets[0]

    def test_wildcard_charset(self):
        accept = 'utf-8; q=0.8, *; q=0.9'
        charsets = ('utf-8', 'utf-16')
        assert select_charset(charsets, accept) == charsets[1]

    def test_iso_8859_1_special_behaviour(self):
        accept = 'utf-8; q=0.8'
        charsets = ('utf-8', 'iso-8859-1')
        assert select_charset(charsets, accept) == charsets[1]
