#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import binascii
from cgi import parse_qs


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
        # The handling of Content-Length is a bit complex. Not all WSGI
        # servers will generate an EOF when reading past the end of the
        # request body. Unfortunately PEP-333 allows this behavior.
        # Therefore we should not read past Content-Length.  An absent
        # Content-Length header does not necessarily mean that there's
        # no request body though, e.g. when using chunked encoding.  See
        # section 4.4 of RFC1616.
        try:
            clen = int(self.header('Content-Length'))
        except (TypeError, ValueError):
            clen = None
        if clen is None:
            encoding = self.header('Transfer-Encoding', 'identity')
            if encoding != 'identity':
                self.content_length = None
            else:
                self.content_length = 0
        else:
            self.content_length = clen
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
        if self.content_length is not None:
            bytes_left = self.content_length - self.bytes_read 
            if size is None or size > bytes_left:
                size = bytes_left
        input = self.environ['wsgi.input']
        data = input.read(size)
        self.bytes_read += len(data)
        return data
