#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import traceback
import httplib as http

from rest.api import request, response, mapper, collection
from rest.filter import InputFilter, OutputFilter, ExceptionHandler
from rest.error import Error


class GenericInputFilter(InputFilter):

    def filter(self, input):
        if request.match.get('action') == '_method_not_allowed':
            headers = [('Allowed', ', '.join(mapper.methods_for(request.path)))]
            print 'headers', headers
            raise Error(http.METHOD_NOT_ALLOWED, headers)
        return input


class GenericOutputFilter(OutputFilter):

    def filter(self, output):
        if output is None:
            return ''
        if isinstance(output, unicode):
            output = output.encode('utf-8')
            ctype = response.header('Content-Type')
            response.set_header(ctype, '%s; charset=UTF-8' % ctype)
        return output


class GenericExceptionHandler(ExceptionHandler):

    def handle(self, exception):
        if isinstance(exception, TypeError):
            text = exception.args[0]
            if text.find('unexpected keyword argument'):
                return Error(http.BAD_REQUEST, reason='unexpected keyword arg')
        elif isinstance(exception, KeyError):
            return Error(http.NOT_FOUND, reason='keyerror exception')
        exception.traceback = traceback.format_exc()
        return exception


class ShowInputFilter(InputFilter):

    def filter(self, input):
        if not input:
            return input
        raise Error(http.BAD_REQUEST, reason='action does not accept input')


class ShowOutputFilter(OutputFilter):

    def filter(self, output):
        if output:
            return output
        raise Error(http.NOT_FOUND, reason='resource not found')


class ListInputFilter(InputFilter):

    def filter(self, input):
        if not input:
            return input
        raise Error(http.BAD_REQUEST, reason='action does not accept input')


class DeleteInputFilter(InputFilter):

    def filter(self, input):
        if not input:
            return input
        raise Error(http.BAD_REQUEST, reason='action does not accept input')


class CreateInputFilter(InputFilter):

    def filter(self, input):
        if input:
            return input
        raise Error(http.BAD_REQUEST, reason='action requires input')


class CreateOutputFilter(OutputFilter):

    def filter(self, output):
        response.status = http.CREATED
        url = response.url_for(collection=collection.name, action='show',
                               id=output)
        response.set_header('Location', url)


class UpdateInputFilter(InputFilter):

    def filter(self, input):
        if input:
            return input
        raise Error(http.BAD_REQUEST, reason='action requires input')


def setup(app):
    app.add_route('/api/:collection', method='GET', action='list')
    app.add_route('/api/:collection', method='POST', action='create')
    app.add_route('/api/:collection/:id', method='DELETE', action='delete')
    app.add_route('/api/:collection/:id', method='GET', action='show')
    app.add_route('/api/:collection/:id', method='PUT', action='update')
    app.add_route('/api/:collection', action='_method_not_allowed')
    app.add_route('/api/:collection/:id', action='_method_not_allowed')
    app.add_input_filter(GenericInputFilter())
    app.add_output_filter(GenericOutputFilter())
    app.add_exception_handler(GenericExceptionHandler())
    app.add_input_filter(ShowInputFilter(), action='show')
    app.add_output_filter(ShowOutputFilter(), action='show')
    app.add_input_filter(ListInputFilter(), action='list')
    app.add_input_filter(DeleteInputFilter(), action='delete')
    app.add_input_filter(CreateInputFilter(), action='create')
    app.add_output_filter(CreateOutputFilter(), action='create')
    app.add_input_filter(UpdateInputFilter(), action='update')
