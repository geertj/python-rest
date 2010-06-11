#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import traceback

from argproc import Error as ArgProcError
from rest import http
from rest.api import request, response, mapper
from rest.error import Error as HTTPReturn
from rest.filter import InputFilter, OutputFilter, ExceptionHandler
from rest.util import make_absolute
from rest.entity import (ParseEntity, FormatEntity, FormatEntityList,
                         TransformResource, ReverseResource,
                         ReverseResourceList)
from rest.resource import Resource


class HandleMethodNotAllowed(InputFilter):
    """Check that the method is allowed for the requested resource."""

    def filter(self, input):
        if request.match.get('action') == '_method_not_allowed':
            headers = [('Allowed', ', '.join(mapper.methods_for(request.path)))]
            raise HTTPReturn(http.METHOD_NOT_ALLOWED, headers)
        return input


class EnsureNoEntity(InputFilter):
    """Assert that no entity is provided by the request."""

    def filter(self, input):
        if input:
            reason = 'Action does not accept any input.'
            raise HTTPReturn(http.BAD_REQUEST, reason=reason)
        return input


class HandleKeyError(ExceptionHandler):
    """KeyError -> 404 NOT FOUND"""

    def handle(self, exception):
        if isinstance(exception, KeyError):
            raise HTTPReturn, http.NOT_FOUND


class HandleCreateOutput(OutputFilter):
    """For the output of the "create" action, set the status to 201
    (CREATED), and add a "Location" header with the correct location of the
    newly created entity."""

    def filter(self, output):
        # XXX: need to distinghuish between "OK" and "not set".
        if response.status == http.OK:
            response.status = http.CREATED
        if isinstance(output, tuple):
            url, object = output
        elif output:
            url, object = output, None
        url = make_absolute(url)
        response.set_header('Location', url)
        # See RFC5023 section 9.2
        if object:
            response.set_header('Content-Location', url)
        return object


class HandleUpdateOutput(OutputFilter):
    """For the output of the "update" action, set the status to 204 (NO
    CONTENT) in case there is no content."""

    def filter(self, output):
        if not output:
            response.status = http.NO_CONTENT
            return ''
        return output


class HandleDeleteOutput(OutputFilter):

    def filter(self, output):
        if output:
            raise HTTPReturn(http.INTERNAL_SERVER_ERROR,
                    reason='Not expecting any output for this action')
        response.status = http.NO_CONTENT
        return ''


class HandleArgProcError(ExceptionHandler):
    """Handle an ArgProc error -> 400 BAD REQUEST."""

    def handle(self, exception):
        if not isinstance(exception, ArgProcError):
            return exception
        format = FormatEntity()
        error = Resource('error')
        error['id'] = 'rest.entity_error'
        error['message'] = str(exception)
        body = format.filter(error)
        headers = response.headers
        raise HTTPReturn(http.BAD_REQUEST, headers=headers, body=body)


def setup_module(app):
    app.add_route('/api/:collection', method='GET', action='list')
    app.add_route('/api/:collection', method='POST', action='create')
    app.add_route('/api/:collection/:id', method='DELETE', action='delete')
    app.add_route('/api/:collection/:id', method='GET', action='show')
    app.add_route('/api/:collection/:id', method='PUT', action='update')
    app.add_route('/api/:collection', action='_method_not_allowed')
    app.add_route('/api/:collection/:id', action='_method_not_allowed')

    app.add_input_filter(HandleMethodNotAllowed(), priority=10)
    app.add_exception_handler(HandleArgProcError())

    app.add_input_filter(EnsureNoEntity(), action='list')
    app.add_output_filter(ReverseResourceList(), action='list')
    app.add_output_filter(FormatEntityList(), action='list')

    app.add_input_filter(EnsureNoEntity(), action='show')
    app.add_output_filter(ReverseResource(), action='show')
    app.add_output_filter(FormatEntity(), action='show')
    app.add_exception_handler(HandleKeyError(), action='show')

    app.add_input_filter(ParseEntity(), action='create')
    app.add_input_filter(TransformResource(), action='create')
    app.add_output_filter(HandleCreateOutput(), action='create')
    app.add_output_filter(ReverseResource(), action='create')
    app.add_output_filter(FormatEntity(), action='create')

    app.add_input_filter(EnsureNoEntity(), action='delete')
    app.add_output_filter(HandleDeleteOutput(), action='delete')
    app.add_exception_handler(HandleKeyError(), action='delete')

    app.add_input_filter(ParseEntity(), action='update')
    app.add_input_filter(TransformResource(), action='update')
    app.add_output_filter(HandleUpdateOutput(), action='update')
    app.add_output_filter(ReverseResource(), action='update')
    app.add_output_filter(FormatEntity(), action='update')
    app.add_exception_handler(HandleKeyError(), action='update')
