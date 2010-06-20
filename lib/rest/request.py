#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import binascii

from rest import http
from rest.http import parse_qs
from rest.error import Error as HTTPReturn


class Request(object):
    """HTTP Request"""

    def __init__(self, env):
        self.environ = env
        self.uri = '%s%s' % (env['SCRIPT_NAME'], env['PATH_INFO'])
        if env['QUERY_STRING']:
            self.uri += '?%s' % env['QUERY_STRING']
        self.method = env['REQUEST_METHOD']
        self.script = env['SCRIPT_NAME']
        self.path = '%s%s' % (env['SCRIPT_NAME'], env['PATH_INFO'])
        args = parse_qs(env['QUERY_STRING'])
        for key in args.keys():
            args[key] = args[key][0]
        self.args = args
        self.server = env['SERVER_NAME']
        self.port = env['SERVER_PORT']
        self.protocol = env['SERVER_PROTOCOL']
        self.user = env.get('REMOTE_USER')
        self.secure = env.get('HTTPS') == 'on'
        self.headers = []
        if env.get('CONTENT_TYPE'):
            self.set_header('Content-Type', env['CONTENT_TYPE'])
        if env.get('CONTENT_LENGTH'):
            self.set_header('Content-Length', env['CONTENT_LENGTH'])
        for key in env:
            if key.startswith('HTTP_'):
                hkey = '-'.join([ x.title() for x in key[5:].split('_')])
                self.set_header(hkey, env[key])
        username = password = None
        try:
            method, auth = self.header('Authorization').split(' ')
            if method == 'Basic':
                username, password = auth.decode('base64').split(':')
        except (AttributeError, ValueError, binascii.Error):
            pass
        self.username = username
        self.password = password
        self.content_length = None
        self.bytes_read = 0

    def header(self, name, default=None):
        for hname,value in self.headers:
            if hname.lower() == name.lower():
                return value
        return default

    def set_header(self, name, value):
        for i in range(len(self.headers)):
            if self.headers[i][0].lower() == name.lower():
                self.headers[i] = (name, value)
                break
        else:
            self.headers.append((name, value))

    def read(self, size=None):
        """Read from the request."""
        if self.content_length is None:
            encoding = self.header('Transfer-Encoding', 'identity')
            if encoding != 'identity':
                raise HTTPReturn(http.NOT_IMPLEMENTED,
                        reason='Unsupported transfer encoding [%s]' % encoding)
            self.content_length = int(self.header('Content-Length', '0'))
        # Make sure we never attempt to read beyond Content-Length, as some
        # WSGI servers will block instead of returning EOF (which is allowed
        # by PEP-333).
        bytes_left = self.content_length - self.bytes_read 
        if size is None or size > bytes_left:
            size = bytes_left
        input = self.environ['wsgi.input']
        data = input.read(size)
        self.bytes_read += len(data)
        return data

    def preferred_content_type(self, content_types):
        """From a list of content types, select the one that is preferred by
        the client based on the value of the "Accept" header."""
        accept_header = self.header('Accept', '*/*')
        return http.select_content_type(content_types, accept_header)

    def preferred_charset(self, charsets):
        """From a list of character sets, select the one that is preferred by
        the client based on the value of the "Accept-Charset" header."""
        accept_header = self.header('Accept-Charset', '*')
        return http.select_content_type(charsets, accept_header)
