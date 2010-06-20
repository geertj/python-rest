#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import sys
import logging
from rest.api import request


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
