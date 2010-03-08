#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.


class Error(Exception):
    """HTTP Error.

    If this exception is raised inside an action method, a corresponding HTTP
    response will be made by the framework.
    """

    def __init__(self, status, headers=[], body='', reason=None):
        self.status = status
        self.headers = headers
        self.body = body
        self.reason = reason
