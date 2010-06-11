#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import inspect
from rest.api import request


class Collection(object):
    """A RESTful collection.

    Methods in this call correspond to RESTful operations on the collection.
    See the documents for this module for more information.
    """

    name = None
    contains = None
    parse_hints = None
    entity_transform = None

    def _method_not_allowed(self):
        """INTERNAL: placeholder for a method that is called with the wrong
        HTTP method."""
        raise NotImplementedError

    def _setup(self):
        """Called just before a request method is called."""

    def _teardown(self):
        """Called after a request has been finished."""

    def _get_namespace(self):
        """Return the global namespace of this collection."""
        module = inspect.getmodule(self)
        return module.__dict__

    def _get_tags(self):
        """Return the tags that are in effect for the argument processing rules
        of this collection."""
        tags = [request.match['action']]
        return tags
