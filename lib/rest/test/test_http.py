#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from rest.http import _parse_header_options, parse_content_type, parse_accept
from nose.tools import assert_raises


class TestParseHeaderOptions(object):

    def test_simple(self):
        options = 'charset=utf8'
        parsed = [('charset', 'utf8')]
        assert _parse_header_options(options) == parsed

    def test_multiple(self):
        options = 'key=value; key2=value2'
        parsed = [('key', 'value'), ('key2', 'value2')]
        assert _parse_header_options(options) == parsed

    def test_empty(self):
        options = ''
        parsed = []
        assert _parse_header_options(options) == parsed

    def test_quoted_value(self):
        options = 'key="value"'
        parsed = [('key', 'value')]
        assert _parse_header_options(options) == parsed

    def test_quoted_value_with_space(self):
        options = 'key="value value"'
        parsed = [('key', 'value value')]
        assert _parse_header_options(options) == parsed

    def test_quoted_value_with_escape(self):
        options = r'key="value\ value"'
        parsed = [('key', 'value value')]
        assert _parse_header_options(options) == parsed

    def test_quoted_value_with_escaped_escape(self):
        options = r'key="value\\value"'
        parsed = [('key', r'value\value')]
        assert _parse_header_options(options) == parsed

    def test_empty_quoted_value(self):
        options = 'key=""'
        parsed = [('key', '')]
        assert _parse_header_options(options) == parsed

    def test_error_empty_key(self):
        options = 'key='
        assert_raises(ValueError, _parse_header_options, options)

    def test_error_empty_value(self):
        options = '=value'
        assert_raises(ValueError, _parse_header_options, options)

    def test_error_missing_quote(self):
        options = r'key="value'
        assert_raises(ValueError, _parse_header_options, options)

    def test_error_missing_escape_error(self):
        options = r'key="value\"'
        assert_raises(ValueError, _parse_header_options, options)


class TestParseContentType(object):

    def test_simple(self):
        ctype = 'text/html'
        parsed = ('text', 'html', [])
        assert parse_content_type(ctype) == parsed

    def test_options(self):
        ctype = 'text/html; charset=utf8'
        parsed = ('text', 'html', [('charset', 'utf8')])
        assert parse_content_type(ctype) == parsed

    def test_multiple_options(self):
        ctype = 'text/html; charset=utf8; foo=bar'
        parsed = ('text', 'html', [('charset', 'utf8'), ('foo', 'bar')])
        assert parse_content_type(ctype) == parsed

    def test_error(self):
        ctype = 'text_html'
        assert_raises(ValueError, parse_content_type, ctype)


class TestParseAccept(object):

    def test_simple(self):
        accept = 'text/html'
        parsed = [('text/html', {})]
        assert parse_accept(accept) == parsed

    def test_parameter(self):
        accept = 'text/html; q=0.2'
        parsed = [('text/html', {'q': '0.2'})]
        assert parse_accept(accept) == parsed

    def test_multiple_parameters(self):
        accept = 'text/html; q=0.2; level=1'
        parsed = [('text/html', {'q': '0.2', 'level': '1'})]
        assert parse_accept(accept) == parsed

    def test_multiple_values(self):
        accept = 'text/html, text/plain'
        parsed = [('text/html', {}), ('text/plain', {})]
        assert parse_accept(accept) == parsed

    def test_priorities(self):
        accept = 'text/plain; q=0.2, text/html'
        parsed = [('text/html', {}), ('text/plain', {'q': '0.2'})]
        assert parse_accept(accept) == parsed

    def test_error_type(self):
        accept = 'text-html'
        assert_raises(ValueError, parse_accept, accept)

    def test_error_parameter(self):
        accept = 'text/html, q=0.2'
        assert_raises(ValueError, parse_accept, accept)
        accept = 'text/html; q==0.2'
        assert_raises(ValueError, parse_accept, accept)
        accept = 'text/html; q 0.2'
        assert_raises(ValueError, parse_accept, accept)

    def test_error_multiple_values(self):
        accept = 'text/html, text/plain; text/xml'
        assert_raises(ValueError, parse_accept, accept)
