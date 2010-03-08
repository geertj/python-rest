#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import threading


class ObjectProxy(object):
    """A simple object proxy that mediates access to a global object in a
    multi-threaded environment."""

    def __init__(self, object=None):
        self.__dict__['____local__'] = threading.local()
        self._register(object)

    def _current_object(self):
        return self.____local__.object

    def _register(self, object):
        self.____local__.object = object

    def _release(self):
        object = self.____local__.object
        del self.____local__.object
        return object

    def __getattr__(self, attr):
        return getattr(self.____local__.object, attr)

    def __setattr__(self, attr, value):
        setattr(self.____local__.object, attr, value)

    def __delattr__(self, attr):
        delattr(self.____local__.object, attr)

    def __setitem__(self, key, value):
        self.____local__.object[key] = value

    def __getitem__(self, key):
        return self.____local__.object[key]

    def __delitem__(self, key):
        del self.____local__.object[key]

    def __call__(self, *args, **kwargs):
        return self.____local__.object(*args, **kwargs)

    def __iter__(self):
        return iter(self.____local__.object)

    def __len__(self):
        return len(self.____local__.object)

    def __contains__(self, elem):
        return elem in self.____local__.object

    def __nonzero__(self):
        return bool(self.____local__.object)

    def __repr__(self):
        return repr(self.____local__.object)
