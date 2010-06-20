#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import sys
import logging
import yaml

from rest.api import request
from rest.resource import Resource


def make_absolute(relurl):
    url = 'https://' if request.secure else 'http://'
    url += request.server
    if request.secure and request.port != 443 or \
            not request.secure and request.port != 80:
        url += ':%s' % request.port
    url += relurl
    return url


def setup_logging(debug):
    """Set up logging."""
    if debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    format = '%(levelname)s [%(name)s] %(message)s'
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)


def import_module(mname):
    try:
        module = __import__(mname)
    except ImportError:
        return
    return sys.modules[mname]


def __construct_resource(loader, node):
    """YAML constructor that constructs a Resource."""
    if isinstance(node, yaml.MappingNode):
        mapping = loader.construct_mapping(node)
        resource = Resource(node.tag[1:], mapping)
    else:
        resource = loader.construct_undefined(node)
    return resource

def _pyyaml_construct_resources():
    """Configure PyYAML so that it will process unknown tags and return a
    Resource instance for them."""
    yaml.Loader.add_constructor(None, __construct_resource)


def __represent_resource(loader, data):
    if '!type' in data:
        data = data.copy()
        tag = '!%s' % data.pop('!type')
    else:
        tag = u'tag:yaml.org,2002:map'
    return loader.represent_mapping(tag, data)

def _pyyaml_represent_resources():
    """Configure PyYAML such that it will represent a Resource instance with a
    !tag corresponding to its type."""
    yaml.Dumper.add_representer(dict, __represent_resource)
    yaml.Dumper.add_representer(Resource, __represent_resource)
