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

from rest import http
from rest.util import _pyyaml_construct_resources, _pyyaml_represent_resources
from rest.error import HTTPReturn
from rest.resource import Resource
from rest.entity.parse import Parser
from rest.entity.format import Formatter

_pyyaml_construct_resources()
_pyyaml_represent_resources()


class YAMLParser(Parser):
    """Parse an entity in YAML format to native representation."""

    def parse(self, input, encoding=None):
        """Parse a YAML entity."""
        # We can ignore the encoding as the YAML spec mandates either UTF-8
        # or UTF-16 with a BOM, which can be autodetected.
        # We use a Loader that turns unrecognized !tags into Resources.
        try:
            parsed = yaml.load(input)
        except YAMLError, e:
            raise HTTPReturn(http.BAD_REQUEST,
                             reason='YAML load error: %s' % str(e))
        return parsed


class YAMLFormatter(Formatter):
    """Format an entity in native representation to YAML."""

    def format(self, object, encoding=None):
        """Format a resource as YAML under the specified encoding."""
        try:
            output = yaml.dump(object, default_flow_style=False,
                               version=(1, 1), encoding=encoding)
        except YAMLError, e:
            raise HTTPReturn(http.INTERNAL_SERVER_ERROR,
                             reason='YAML dump error: %s' % str(e))
        return output
