#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from rest import http
from rest.api import request, response
from rest.error import HTTPReturn


class Formatter(object):
    """Base class for entity formatters."""

    def format(self, object, encoding=None):
        raise NotImplementedError
        

class FormatterManager(object):

    formatters = {}

    @classmethod
    def add_formatter(self, content_type, formatter):
        self.formatters[content_type] = formatter

    def format(self, object):
        """Format an entity."""
        if not isinstance(object, dict) and not isinstance(object, list):
            return object
        accept = request.header('Accept', '*/*')
        ctype = http.select_content_type(self.formatters.keys(), accept)
        if not ctype:
            raise HTTPReturn(http.NOT_ACCEPTABLE,
                    reason='No acceptable content-type in: %s' % accept)
        accept = request.header('Accept-Charset', '*')
        charset = http.select_charset(('utf-8',), accept)
        if not charset:
            raise HTTPReturn(http.NOT_ACCEPTABLE,
                    reason='No acceptable charset in: %s' % accept)
        formatter = self.formatters[ctype]
        output = formatter.format(object, charset)
        response.set_header('Content-Type', '%s; charset=%s' % (ctype, charset))
        response.set_header('Content-Length', str(len(output)))
        return output
