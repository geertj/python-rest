#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import traceback
import httplib as http
from rest.error import Error


class InputFilter(object):
    """Base class for input filters."""

    def filter(self, input, request, response):
        raise NotImplementedError


class OutputFilter(object):
    """Base class for output filters."""

    def filter(self, output, request, response):
        raise NotImplementedError


class ExceptionHandler(object):
    """Base class for exception handlerss."""

    def handle(self, exception, request, response):
        raise NotImplementedError


class ReturnIfInput(InputFilter):
    """Return a HTTP status if there is any input to the HTTP request."""

    def __init__(self, status):
        self.status = status

    def filter(self, input, request, response):
        if input:
            raise Error, self.status
        return input


class ReturnIfNoInput(InputFilter):
    """Return a HTTP status if there is no input to the HTTP request."""

    def __init__(self, status):
        self.status = status

    def filter(self, input, request, response):
        if not input or not response.header('Content-Type'):
            raise Error, self.status
        return input


class ReturnIfNoOutput(OutputFilter):
    """Return a HTTP status if there is no output in the HTTP response."""

    def __init__(self, status):
        self.status = status

    def filter(self, output, request, response):
        if not output:
            response.status = self.status
        return output


class HandleCreateOutput(OutputFilter):
    """Handle the output of a "create" action."""

    def filter(self, output, request, response):
        response.status = http.CREATED
        url = response.url_for(collection=request.match['collection'],
                               action='show', id=output)
        response.set_header('Location', url)
        return ''


class ConvertUnicodeToBytes(OutputFilter):
    """Covert unicode output to bytes."""

    def filter(self, output, request, response):
        if isinstance(output, unicode):
            output = output.encode('utf-8')
            ctype = response.header('Content-Type')
            response.set_header(ctype, '%s; charset=UTF-8' % ctype)
        return output


class ConvertNoneToEmptyString(OutputFilter):
    """Covert None to an empty string."""

    def filter(self, output, request, response):
        if output is None:
            return ''
        return output


class OnExceptionReturn(ExceptionHandler):
    """If an exception occurred, return a HTTP status."""

    def __init__(self, exception, status):
        self.exception = exception
        self.status = status

    def handle(self, exception, request, response):
        if isinstance(exception, self.exception):
            raise Error, self.status


class OnUnexpectedKeywordReturn(ExceptionHandler):
    """Return a HTTP status if an unexpected keyword exception occurs."""

    def __init__(self, status):
        self.status = status

    def handle(self, exception, request, response):
        if isinstance(exception, TypeError):
            text = exception.args[0]
            if text.find('unexpected keyword argument'):
                raise Error, self.status


class OnExceptionReRaise(ExceptionHandler):
    """Re-raise if an exception occurs."""

    def handle(self, exception, request, response):
        exception.traceback = traceback.format_exc()
        raise exception


class CheckMappingErrors(InputFilter):
    """Check for errors during the mapping process."""

    def filter(self, input, request, response):
        if request.match.get('action') == 'method_error':
            headers = [('Allowed', request.match['allowed'].encode('ascii'))]
            raise Error(http.METHOD_NOT_ALLOWED, headers)
        return input
