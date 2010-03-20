#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import httplib as http
from rest import Response
from rest.test.test_request import environ


class TestResponse(object):

    def test_basic(self):
        response = Response(environ)
        assert response.status == http.OK
        assert response.header('Content-Type') == 'text/plain'

    def test_headers(self):
        response = Response(environ)
        assert len(response.headers) == 1
        response.set_header('Content-Type', 'text/xml')
        assert len(response.headers) == 1
        assert response.header('Content-Type') == 'text/xml'
        assert response.header('Header-1') is None
        response.set_header('Header-1', 'value1')
        assert response.header('Header-1') == 'value1'
        assert response.header('header-1') == 'value1'
        assert response.header('HEADER-1') == 'value1'
        assert len(response.headers) == 2
