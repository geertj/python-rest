#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.


class Collection(object):
    """A RESTful collection.

    Methods in this call correspond to RESTful operations on the collection.
    See the documents for this module for more information.
    """

    name = None

    def _setup(self):
        """Called just before a request method is called."""

    def _teardown(self):
        """Called after a request has been finished."""
