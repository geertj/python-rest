#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import traceback

from rest import http
from rest.api import request, response, mapper
from rest.error import Error
from rest.filter import InputFilter, OutputFilter, ExceptionHandler
from rest.util import issequence


class AssertMethodAllowed(InputFilter):
    """Check that the current method is allowed for the current resource."""

    def filter(self, input):
        if request.match.get('action') == '_method_not_allowed':
            headers = [('Allowed', ', '.join(mapper.methods_for(request.path)))]
            raise Error(http.METHOD_NOT_ALLOWED, headers)
        return input


class AssertInputFormat(InputFilter):
    """Check that the request entity is of a certain MIME type."""

    def __init__(self, content_type):
        if not issequence(content_type):
            content_type = [content_type]
        self.content_types = content_type

    def filter(self, input):
        ctype = request.header('Content-Type')
        if ctype and ctype not in self.content_types:
            reason = 'Unsupported content-type provided by client.'
            raise Error(http.UNSUPPORTED_MEDIA_TYPE, reason=reason)
        return input


class AssertAcceptableOutputFormat(InputFilter):
    """Check if the encoding that the client provides as acceptable are
    availble for a certain resource."""

    def __init__(self, content_type):
        if not issequence(content_type):
            content_type = [content_type]
        self.content_types = content_type

    def _acceptable_content_type(self, atype):
        atype, asubtype = atype.split('/')
        for ctype in self.content_types:
            type, subtype = ctype.split('/')
            if atype == '*' or atype == type and \
                    asubtype == '*' or asubtype == subtype:
                return True
        return False

    def filter(self, input):
        accept = request.header('Accept')
        if not accept:
            return input
        accept = http.parse_accept(accept)
        for type,params in accept:
            if self._acceptable_content_type(type):
                break
        else:
            reason = 'Unsupported content-type requested by client.'
            raise Error(http.NOT_ACCEPTABLE, reason=reason)
        return input


class AssertNoInput(InputFilter):
    """Assert that no entity is provided by the request."""

    def filter(self, input):
        if input:
            reason = 'Action does not accept any input.'
            raise Error(http.BAD_REQUEST, reason=reason)
        return input


class AssertHasInput(InputFilter):
    """Assert the request contains a request entity and a content type."""

    def filter(self, input):
        if not input:
            reason = 'No input was provided.'
            raise Error(http.BAD_REQUEST, reason=reason)
        ctype = request.header('Content-Type')
        if ctype is None:
            reason = 'Content-Type header was not provided.'
            raise Error(http.BAD_REQUEST, reason=reason)
        return input


class ProcessNoneOutput(OutputFilter):
    """If the output is "None", convert it to an empty string ("")."""

    def filter(self, output):
        if output is None:
            output = ''
        return output


class ProcessUnicodeOutput(OutputFilter):
    """If the output is unicode, encode it as UTF-8 and set the correct
    encoding on the response."""

    def filter(self, output):
        if isinstance(output, unicode):
            output = output.encode('utf-8')
            ctype = response.header('Content-Type')
            response.set_header(ctype, '%s; charset=UTF-8' % ctype)
        return output


class ProcessEmptyOutput(OutputFilter):
    """In case of no output, raise a 404 (NOT_FOUND) HTTP error."""

    def filter(self, output):
        if not output:
            raise Error(http.NOT_FOUND, reason='resource not found')
        return output


class HandleCommonExceptions(ExceptionHandler):
    """Handle common exceptions. KeyError is mapped to 404 (NOT_FOUND), other
    exceptions are mapped to 400 (BAD_REQUEST)."""

    def handle(self, exception):
        if isinstance(exception, TypeError) \
                or isinstance(exception, ValueError):
            return Error(http.BAD_REQUEST, reason=str(exception))
        elif isinstance(exception, KeyError):
            return Error(http.NOT_FOUND, reason=str(exception))
        exception.traceback = traceback.format_exc()
        return exception


class ProcessCreateOutput(OutputFilter):
    """For the output of the "create" action, set the status to 201
    (CREATED), and add a "Location" header with the correct location of the
    newly created entity."""

    def filter(self, output):
        if not output:
            return output
        response.status = http.CREATED
        if isinstance(output, tuple):
            url, object = output
        elif output:
            url, object = output, ''
        response.set_header('Location', url)
        # See RFC5023 section 9.2
        if object:
            response.set_header('Content-Location', url)
        return object


class ProcessUpdateOutput(OutputFilter):
    """For the output of the "update" action, set the status to 204 (NO
    CONTENT) in case there is no content."""

    def filter(self, output):
        if not output:
            response.status = http.NO_CONTENT
        return output


class ProcessLocationHeader(OutputFilter):
    """Make the "Location" and "Content-Location" headers on the HTTP response
    absolute URLs. RFC2616 requires that "Location" is an aboslute URL."""

    def _make_absolute(self, relurl):
        url = 'https://' if request.secure else 'http://'
        url += request.server
        if request.secure and request.port != 443 or \
                not request.secure and request.port != 80:
            url += ':%s' % request.port
        url += relurl
        return url

    def filter(self, output):
        location = response.header('Location')
        if location and not location.startswith('http'):
            url = self._make_absolute(location)
            response.set_header('Location', url)
        location = response.header('Content-Location')
        if location and not location.startswith('http'):
            url = self._make_absolute(location)
            response.set_header('Content-Location', url)
        return output


def setup_module(app):
    app.add_route('/api/:collection', method='GET', action='list')
    app.add_route('/api/:collection', method='POST', action='create')
    app.add_route('/api/:collection/:id', method='DELETE', action='delete')
    app.add_route('/api/:collection/:id', method='GET', action='show')
    app.add_route('/api/:collection/:id', method='PUT', action='update')
    app.add_route('/api/:collection', action='_method_not_allowed')
    app.add_route('/api/:collection/:id', action='_method_not_allowed')

    app.add_input_filter(AssertMethodAllowed())
    app.add_output_filter(ProcessNoneOutput(), priority=10)
    app.add_output_filter(ProcessUnicodeOutput(), priority=90)
    app.add_output_filter(ProcessLocationHeader(), priority=90)
    app.add_exception_handler(HandleCommonExceptions())

    app.add_input_filter(AssertNoInput(), action=['show', 'list', 'delete'])
    app.add_output_filter(ProcessEmptyOutput(), action='show')
    app.add_input_filter(AssertHasInput(), action=['create', 'update'])
    app.add_output_filter(ProcessCreateOutput(), action='create', priority=10)
    app.add_output_filter(ProcessUpdateOutput(), action='update', priority=10)
