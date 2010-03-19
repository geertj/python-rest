#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from rest.http import parse_accept
from nose.tools import assert_raises


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
