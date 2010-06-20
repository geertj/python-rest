#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.


class InputFilter(object):
    """Base class for input filters."""

    def filter(self, input):
        raise NotImplementedError


class OutputFilter(object):
    """Base class for output filters."""

    def filter(self, output):
        raise NotImplementedError


class ExceptionHandler(object):
    """Base class for exception handlerss."""

    def handle(self, exception):
        raise NotImplementedError
