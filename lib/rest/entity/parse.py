#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from rest import http
from rest.api import request
from rest.error import HTTPReturn


class Parser(object):
    """Base class for entity parsers."""

    def parse(self, input, encoding=None):
        raise NotImplementedError


class ParserManager(object):
    """Parser manager. Contains a collection of available parsers."""

    def __init__(self):
        self.parsers = {}

    def add_parser(self, content_type, parser):
        """Add a parser for a content type."""
        self.parsers[content_type] = parser

    def parse(self, input):
        """Parse an entity."""
        ctype = request.header('Content-Type')
        if not ctype:
            raise HTTPReturn(http.BAD_REQUEST,
                    reason='Missing Content-Type header')
        try:
            type, subtype, options = http.parse_content_type(ctype)
        except ValueError:
            raise HTTPReturn(http.BAD_REQUEST,
                    reason='Illegal Content-Type header [%s]' % ctype)
        ctype = '%s/%s' % (type, subtype)
        encoding = options.get('charset')
        if not len(input):
            raise HTTPReturn(http.BAD_REQUEST,
                    reason='No request entity provided')
        if ctype not in self.parsers:
            raise HTTPReturn(http.UNSUPPORTED_MEDIA_TYPE,
                             reason='Content-Type not supported [%s]' % ctype)
        parser = self.parsers[ctype]
        parsed = parser.parse(input, encoding)
        return parsed
