#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import traceback

from rest import http
from rest.api import request, response, mapper, collection
from rest.error import Error


HIGHEST = 1
HIGHER = 25
NORMAL = 50
LOWER = 75
LOWEST = 99


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


class CheckMethodAllowed(InputFilter):

    def filter(self, input):
        if request.match.get('action') == '_method_not_allowed':
            headers = [('Allowed', ', '.join(mapper.methods_for(request.path)))]
            raise Error(http.METHOD_NOT_ALLOWED, headers)
        return input


class HandleNoneOutput(OutputFilter):

    def filter(self, output):
        if output is None:
            return ''
        return output

class ConvertUnicodeToBytes(OutputFilter):

    def filter(self, output):
        if isinstance(output, unicode):
            output = output.encode('utf-8')
            ctype = response.header('Content-Type')
            response.set_header(ctype, '%s; charset=UTF-8' % ctype)
        return output


class HandleCommonExceptions(ExceptionHandler):

    def handle(self, exception):
        if isinstance(exception, TypeError) \
                or isinstance(exception, ValueError):
            return Error(http.BAD_REQUEST, reason=str(exception))
        elif isinstance(exception, KeyError):
            return Error(http.NOT_FOUND, reason=str(exception))
        exception.traceback = traceback.format_exc()
        return exception


class AssertNoInput(InputFilter):

    def filter(self, input):
        if not input:
            return input
        raise Error(http.BAD_REQUEST, reason='action does not accept input')


class RequireInput(InputFilter):

    def filter(self, input):
        if not input:
            raise Error(http.BAD_REQUEST, reason='action requires input')
        return input


class NotFoundIfNoResponse(OutputFilter):

    def filter(self, output):
        if output:
            return output
        raise Error(http.NOT_FOUND, reason='resource not found')


class SetLocationHeader(OutputFilter):

    def filter(self, output):
        response.status = http.CREATED
        url = response.url_for(collection=collection.name, action='show',
                               id=output)
        response.set_header('Location', url)
        return ''


class RequireContentType(InputFilter):

    def __init__(self, ctype):
        if isinstance(ctype, list) or isinstance(ctype, tuple):
            self.content_type = ctype
        else:
            self.content_type = [ctype]

    def filter(self, input):
        ctype = request.header('Content-Type')
        if ctype not in self.content_type:
            raise Error(http.UNSUPPORTED_MEDIA_TYPE)
        return input
