# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.


class Resource(dict):
    """A REST Resource.

    Resources and collections are the central concepts in REST. A resource
    represents one object and is part of a collection.

    A resource is just a Python dictionary with a few special requirements.
    These requirements should normally not get in your way, but they ensure
    that serialization / deserialization to mutiple formats becomes easier.

     - A Resource has a type, stored in the '!type' key.
     - All keys are strings.
     - All values are either scalars, lists, or Resources.

     The requirements are currently not enforced. Think of it as a protocol to
     which you (the programmer) are bound.
     """

    def __init__(self, type, *args, **kwargs):
        super(Resource, self).__init__()
        for arg in args:
            self.update(arg)
        self.update(**kwargs)
        self['!type'] = type
