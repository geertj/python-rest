#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from __future__ import absolute_import

import re
from xml.etree import ElementTree as etree
from xml.etree.ElementTree import Element
from xml.parsers.expat import ExpatError

from rest.api import collection
from rest.error import HTTPReturn
from rest.resource import Resource
from rest.entity.parse import Parser
from rest.entity.format import Formatter
from rest.entity.hint import Hints


class XMLParser(Parser):
    """Parse an XML Entity."""

    def _convert(self, node, path=[]):
        """Convert an XML node into its native representation (a string,
        a list, or a Resource)."""
        if len(node) == 0:
            return node.text
        has_duplicates = len(set((child.tag for child in node))) != len(node)
        if has_duplicates or self.hints.get(path).get('sequence'):
            result = []
            path.append(None)
            for ix,child in enumerate(node):
                path[-1] = '[%d]' % ix
                result.append(self._convert(child, path))
            del path[-1]
        else:
            result = Resource(node.tag)
            path.append(None)
            for child in node:
                path[-1] = child.tag
                result[child.tag] = self._convert(child, path)
            del path[-1]
        return result

    _re_preamble_start = re.compile(r'<\?xml', re.I)
    _re_preamble_end = re.compile(r'\?>')

    def parse(self, input, encoding=None):
        """Parse XML from `input' according to `encoding'."""
        if encoding and self._re_preamble_start.match(input):
            # The encoding from the HTTP header takes precedence. The preamble
            # is the only way in which we can pass it on to ElementTree.
            preamble = '<?xml version="1.0" encoding="%s" ?>' % encoding
            mobj = self._re_preamble_end.search(input)
            if mobj == None:
                raise HTTPReturn(http.BAD_REQUEST, reason='Illegal XML input')
            input = input[mobj.end()+1:]
        elif not encoding and not self._re_preamble_start.match(input):
            # RFC2616 section 3.7.1
            preamble = '<?xml version="1.0" encoding="utf-8" ?>'
        else:
            preamble = ''
        try:
            root = etree.fromstring(preamble + input)
        except ExpatError, err:
            raise HTTPReturn(http.BAD_REQUEST,
                             reason='XML Error: %s' % str(err))
        hints = Hints()
        hints.add_hints(getattr(collection, 'parse_hints', ''))
        self.hints = hints
        resource = self._convert(root)
        return resource


class XMLFormatter(Formatter):
    """Format an entity into a XML representation."""

    def _format(self, value, type=None):
        """Convert a resource into an XML node."""
        if isinstance(value, dict):
            if type is None:
                type = value.get('!type')
                if not type:
                    return
            if '!type' in value:
                value = value.copy()
                del value['!type']
            node = Element(type)
            for key in value:
                child = self._format(value[key], key)
                if child is None:
                    continue
                node.append(child)
        elif isinstance(value, list):
            node = Element(type)
            for elem in value:
                child = self._format(elem, None)
                if child is None:
                    continue
                node.append(child)
        elif isinstance(value, basestring):
            node = Element(type)
            node.text = value
        elif value is None:
            node = Element(type)
        else:
            node = Element(type)
            node.text = str(value)
        return node

    def _indent(self, node, level):
        """Indent a DOM tree."""
        if not len(node):
            return
        level += 2
        node.text = '\n' + level*' '
        for ix,child in enumerate(node):
            if ix == len(node)-1:
                child.tail = '\n' + (level - 2)*' '
            else:
                child.tail = '\n' + level*' '
            self._indent(child, level)

    def format(self, output, encoding=None):
        """Convert the resource `output' into XML under the specified
        encoding."""
        if isinstance(output, dict):
            root = self._format(output)
        elif isinstance(output, list):
            root = Element(collection.name)
            for elem in output:
                child = self._format(elem)
                if child:
                    root.append(child)
        self._indent(root, 0)
        output = '<?xml version="1.0" encoding="%s" ?>\n' % encoding
        output += etree.tostring(root, encoding=encoding)
        return output
