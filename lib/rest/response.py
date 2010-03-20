#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from rest import http
from rest.api import mapper


class Response(object):
    """HTTP Response"""

    def __init__(self, environ):
        self.environ = environ
        self.status = http.OK
        self.headers = [('Content-Type', 'text/plain')]

    def header(self, name):
        for hname,value in self.headers:
            if hname.lower() == name.lower():
                return value

    def set_header(self, name, value):
        for i in range(len(self.headers)):
            if self.headers[i][0].lower() == name.lower():
                self.headers[i] = (name, value)
                break
        else:
            self.headers.append((name, value))

    def url_for(self, collection=None, action=None, **kwargs):
        kwargs['collection'] = collection
        kwargs['action'] = action
        if self.environ.get('HTTPS') == 'on':
            scheme = 'https'
        else:
            scheme = 'http'
        path = mapper.url_for(**kwargs)
        url = '%s://%s%s' % (scheme, self.environ['SERVER_NAME'], path)
        return url
