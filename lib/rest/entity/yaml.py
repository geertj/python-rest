#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from __future__ import absolute_import

import yaml
from yaml import YAMLError
from StringIO import StringIO

from rest.error import HTTPReturn
from rest.resource import Resource
from rest.entity.parse import Parser
from rest.entity.format import Formatter


class YAMLParser(Parser):
    """Parse an entity in YAML format to native representation."""

    def _construct(self, loader):
        """Construct a resource node."""
        def construct(self, node):
            if isinstance(node, yaml.MappingNode):
                mapping = loader.construct_mapping(node)
                resource = Resource(node.tag[1:], mapping)
            return resource
        return construct

    def parse(self, input, encoding=None):
        """Parse a YAML entity."""
        # We can ignore the encoding as the YAML spec mandates either UTF-8
        # or UTF-16 with a BOM, which can be autodetected.
        # We use a Loader that turns unrecognized !tags into Resources.
        loader = yaml.Loader(input)
        loader.add_constructor(None, self._construct(loader))
        try:
            parsed = loader.get_single_data()
        except YAMLError, e:
            raise HTTPReturn(http.BAD_REQUEST,
                             reason='YAML Error: %s' % str(e))
        return parsed


class YAMLFormatter(Formatter):
    """Format an entity in native representation to YAML."""

    def _represent_resource(self, loader):
        """Used as a YAML representer for dictionaries."""
        def format(self, data):
            if '!type' in data:
                data = data.copy()
                tag = '!%s' % data.pop('!type')
            else:
                tag = u'tag:yaml.org,2002:map'
            return loader.represent_mapping(tag, data)
        return format

    def format(self, object, encoding=None):
        """Format a resource as YAML under the specified encoding."""
        stream = StringIO()
        dumper = yaml.Dumper(stream, default_flow_style=False, version=(1,1),
                             encoding=encoding)
        dumper.add_representer(dict, self._represent_resource(dumper))
        dumper.add_representer(Resource, self._represent_resource(dumper))
        dumper.open()
        try:
            dumper.represent(object)
        except YAMLError, e:
            raise HTTPReturn(http.INTERNAL_SERVER_ERROR,
                             reason='YAML dump error: %s' % str(e))
        dumper.close()
        return stream.getvalue()
