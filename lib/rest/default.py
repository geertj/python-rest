#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import traceback
import httplib as http

from rest import api
from rest.filter import InputFilter, OutputFilter, ExceptionHandler
from rest.mapper import Route
from rest.error import Error


class GenericInputFilter(InputFilter):

    def filter(self, input):
        if api.request.match.get('action') == 'method_error':
            headers = [('Allowed', api.request.match['allowed'].encode('ascii'))]
            raise Error(http.METHOD_NOT_ALLOWED, headers)
        return input

class GenericOutputFilter(OutputFilter):

    def filter(self, output):
        if output is None:
            return ''
        if isinstance(output, unicode):
            output = output.encode('utf-8')
            ctype = api.response.header('Content-Type')
            api.response.set_header(ctype, '%s; charset=UTF-8' % ctype)
        return output

class GenericExceptionHandler(ExceptionHandler):

    def handle(self, exception):
        if isinstance(exception, TypeError):
            text = exception.args[0]
            if text.find('unexpected keyword argument'):
                return Error(http.BAD_REQUEST, reason='unexpected keyword arg')
        exception.traceback = traceback.format_exc()
        return exception


class UnsupportedMethodRoute1(Route):

    path = '/api/:collection'
    methods = ['PUT', 'DELETE']
    args ={ 'action': 'method_error', 'allowed': 'GET, POST' }

class UnsupportedMethodRoute2(Route):

    path = '/api/:collection/:id'
    methods = ['POST']
    args ={ 'action': 'method_error', 'allowed': 'GET, DELETE, PUT' }


class ShowInputFilter(InputFilter):

    action = 'show'

    def filter(self, input):
        if not input:
            return input
        raise Error(http.BAD_REQUEST, reason='action does not accept input')

class ShowOutputFilter(OutputFilter):

    action = 'show'

    def filter(self, output):
        if output:
            return output
        raise Error(http.NOT_FOUND, reason='resource not found')

class ShowRoute(Route):

    path = '/api/:collection/:id'
    methods = ['GET']
    args ={ 'action': 'show' }


class ListInputFilter(InputFilter):

    action = 'list'

    def filter(self, input):
        if not input:
            return input
        raise Error(http.BAD_REQUEST, reason='action does not accept input')

class ListRoute(Route):

    path = '/api/:collection'
    methods = ['GET']
    args ={ 'action': 'list' }


class DeleteInputFilter(InputFilter):

    action = 'delete'

    def filter(self, input):
        if not input:
            return input
        raise Error(http.BAD_REQUEST, reason='action does not accept input')

class DeleteExceptionHandler(ExceptionHandler):

    action = 'delete'

    def handle(self, exception):
        if isinstance(exception, KeyError):
            return Error(http.NOT_FOUND)
        return exception

class DeleteRoute(Route):

    path = '/api/:collection/:id'
    methods = ['DELETE']
    args ={ 'action': 'delete' }


class CreateInputFilter(InputFilter):

    action = 'create'

    def filter(self, input):
        if input:
            return input
        raise Error(http.BAD_REQUEST, reason='action requires input')

class CreateOutputFilter(OutputFilter):

    action = 'create'

    def filter(self, output):
        api.response.status = http.CREATED
        url = api.response.url_for(collection=api.request.match['collection'],
                                   action='show', id=output)
        api.response.set_header('Location', url)

class CreateRoute(Route):

    path = '/api/:collection'
    methods = ['POST']
    args ={ 'action': 'create' }


class UpdateInputFilter(InputFilter):

    action = 'update'

    def filter(self, input):
        if input:
            return input
        raise Error(http.BAD_REQUEST, reason='action requires input')

class UpdateExceptionHandler(ExceptionHandler):

    action = 'update'

    def handle(self, exception):
        if isinstance(exception, KeyError):
            return Error(http.NOT_FOUND)
        return exception

class UpdateRoute(Route):

    path = '/api/:collection/:id'
    methods = ['PUT']
    args ={ 'action': 'update' }
