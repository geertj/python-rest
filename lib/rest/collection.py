#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import inspect


class Collection(object):
    """A RESTful collection.

    Methods in this call correspond to RESTful operations on the collection.
    See the documents for this module for more information.
    """

    name = None

    def _method_not_allowed(self):
        """INTERNAL: placeholder for a method that is called with the wrong
        HTTP method."""
        raise NotImplementedError

    def setup(self):
        """Called just before a request method is called."""

    def teardown(self):
        """Called after a request has been finished."""

    def _get_namespace(self):
        """Return the global namespace of this collection."""
        module = inspect.getmodule(self)
        return module.__dict__
