#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from __future__ import absolute_import

import json
from json import JSONEncoder

from rest import http
from rest.error import HTTPReturn
from rest.entity.parse import Parser
from rest.entity.format import Formatter


class JSONParser(Parser):
    """Parse an entity in JSON format to native representation."""

    def parse(self, input, encoding):
        """Parse a JSON entity."""
        try:
            parsed = json.loads(input, encoding)
        except ValueError, err:
            raise HTTPReturn(http.BAD_REQUEST,
                             reason='JSON parsing error: %s' % str(err))
        return parsed


class ResourceEncoder(JSONEncoder):
    
    def default(self, object):
        if isinstance(object, dict) and '!type' in dict:
            copy = object.copy()
            del object['!type']
        return JSONEncoder.default(self, object)


class JSONFormatter(Formatter):
    """Format an entity in native representation to YAML."""

    def format(self, object, encoding=None):
        """Format a resource as JSON under the specified encoding."""
        encoder = ResourceEncoder()
        output = json.dumps(object, encoding=encoding, cls=ResourceEncoder)
        return output
