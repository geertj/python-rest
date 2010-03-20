#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from rest import Request


environ = {
    'REQUEST_URI': '/foo/bar/baz?arg=val&arg2=val%202',
    'REQUEST_METHOD': 'GET',
    'SERVER_NAME': 'localhost',
    'SERVER_PORT': '8080',
    'SCRIPT_NAME': '/foo',
    'PATH_INFO': '/bar/baz',
    'QUERY_STRING': 'arg=val&arg2=val%202',
    'SERVER_PROTOCOL': 'HTTP/1.1',
    'REMOTE_USER': 'jbloggs',
    'HTTPS': 'off',
    'CONTENT_LENGTH': '20',
    'CONTENT_TYPE': 'text/plain',
    'HTTP_HEADER_1': 'value1',
    'HTTP_HEADER_2': 'value2'
}


class TestRequest(object):

    def test_attributes(self):
        request = Request(environ)
        assert request.uri == '/foo/bar/baz?arg=val&arg2=val%202'
        assert request.method == 'GET'
        assert request.script == '/foo'
        assert request.path == '/foo/bar/baz'
        assert request.args == { 'arg': 'val', 'arg2': 'val 2' }
        assert request.protocol == 'HTTP/1.1'
        assert not request.secure
        assert ('Content-Length', '20') in request.headers
        assert ('Content-Type', 'text/plain') in request.headers
        assert ('Header-1', 'value1') in request.headers
        assert ('Header-2', 'value2') in request.headers

    def test_headers(self):
        request = Request(environ)
        assert len(request.headers) == 4
        request.set_header('Content-Type', 'text/xml')
        assert len(request.headers) == 4
        assert request.header('Content-Type') == 'text/xml'
        assert request.header('Header-3') is None
        request.set_header('Header-3', 'value3')
        assert request.header('Header-3') == 'value3'
        assert request.header('header-3') == 'value3'
        assert request.header('HEADER-3') == 'value3'
        assert len(request.headers) == 5
