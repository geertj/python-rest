#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import logging
import traceback
import httplib as http

from rfc822 import formatdate
from routes import Mapper

import rest
from rest.request import Request
from rest.response import Response
from rest.error import Error
from rest.filter import *


class Application(object):
    """A WSGI Application that implements a RESTful API."""

    def __init__(self, environ, start_response):
        """Constructor."""
        self.environ = environ
        self.start_response = start_response
        self.collections = {}
        self.mapper = Mapper()
        self.mapper.environ = environ
        self.input_filters = {}
        self.output_filters = {}
        self.exception_handlers = {}
        self.logger = logging.getLogger('rest')
        self.setup_collections()
        self.setup_filters()
        self.setup_routes()
        self.mapper.create_regs()

    def add_collection(self, collection):
        """Add a single collection."""
        self.collections[collection.name] = collection

    def setup_collections(self):
        """Setup all the collections. You can change the defaults by
        overriding this method in your application."""
        self.add_collection(RootCollection())

    def add_input_filter(self, controller, action, filter, position=None):
        """Add an input filter."""
        key = (controller, action)
        if key not in self.input_filters:
            self.input_filters[key] = []
        if position is None:
            self.input_filters[key].append(filter)
        else:
            self.input_filters[key].insert(position, filter)

    def add_output_filter(self, controller, action, filter, position=None):
        """Add an output filter."""
        key = (controller, action)
        if key not in self.output_filters:
            self.output_filters[key] = []
        if position is None:
            self.output_filters[key].append(filter)
        else:
            self.output_filters[key].insert(position, filter)

    def add_exception_handler(self, controller, action, handler, position=None):
        """Add an exception handler."""
        key = (controller, action)
        if key not in self.exception_handlers:
            self.exception_handlers[key] = []
        if position is None:
            self.exception_handlers[key].append(handler)
        else:
            self.exception_handlers[key].insert(position, handler)

    def setup_filters(self):
        """Set up the filters. You can change the defaults by overriding this
        method in your application."""
        self.add_input_filter(None, 'show', ReturnIfInput(http.BAD_REQUEST))
        self.add_output_filter(None, 'show',
                    ReturnIfNoOutput(http.NOT_FOUND))
        self.add_input_filter(None, 'list', ReturnIfInput(http.BAD_REQUEST))
        self.add_input_filter(None, 'delete', ReturnIfInput(http.BAD_REQUEST))
        self.add_exception_handler(None, 'delete',
                    OnExceptionReturn(KeyError, http.NOT_FOUND))
        self.add_input_filter(None, 'create', ReturnIfNoInput(http.BAD_REQUEST))
        self.add_output_filter(None, 'create', ReturnIfNoOutput(http.BAD_REQUEST))
        self.add_output_filter(None, 'create', HandleCreateOutput())
        self.add_input_filter(None, 'update', ReturnIfNoInput(http.BAD_REQUEST))
        self.add_exception_handler(None, 'update',
                    OnExceptionReturn(KeyError, http.NOT_FOUND))
        self.add_input_filter(None, None, CheckMappingErrors())
        self.add_exception_handler(None, None,
                    OnUnexpectedKeywordReturn(http.BAD_REQUEST))
        self.add_exception_handler(None, None, OnExceptionReRaise())
        self.add_output_filter(None, None, ConvertNoneToEmptyString())
        self.add_output_filter(None, None, ConvertUnicodeToBytes())

    def filter_input(self, input, request, response):
        """Filter input."""
        controller = request.match['controller']
        action = request.match['action']
        filters = self.input_filters.get((controller, action), [])
        filters += self.input_filters.get((None, action), [])
        filters += self.input_filters.get((controller, None), [])
        filters += self.input_filters.get((None, None), [])
        for filter in filters:
            input = filter.filter(input, request, response)
        return input

    def filter_output(self, output, request, response):
        """Filter input."""
        controller = request.match['controller']
        action = request.match['action']
        filters = self.output_filters.get((controller, action), [])
        filters += self.output_filters.get((None, action), [])
        filters += self.output_filters.get((controller, None), [])
        filters += self.output_filters.get((None, None), [])
        for filter in filters:
            output = filter.filter(output, request, response)
        return output

    def handle_exception(self, exception, request, response):
        """Handle an exception."""
        controller = request.match['controller']
        action = request.match['action']
        handlers = self.exception_handlers.get((controller, action), [])
        handlers += self.exception_handlers.get((None, action), [])
        handlers += self.exception_handlers.get((controller, None), [])
        handlers += self.exception_handlers.get((None, None), [])
        for handler in handlers:
            handler.handle(exception, request, response)

    def add_route(self, *args, **kwargs):
        """Add a route."""
        self.mapper.connect(*args, **kwargs)

    def setup_routes(self):
        """Set up the default routes. You can change the default by overriding
        this method in your applications."""
        self.add_route('/api', collection='root', action='list',
                       conditions={'method': ['GET']})
        self.add_route('/api/:collection', action='list',
                       conditions={'method': ['GET']})
        self.add_route('/api/:collection', action='create',
                       conditions={'method': ['POST']})
        self.add_route('/api/:collection', action='method_error',
                       allowed='GET, POST')
        self.add_route('/api/:collection/:id', action='show',
                       conditions={'method': ['GET']})
        self.add_route('/api/:collection/:id', action='delete',
                       conditions={'method': ['DELETE']})
        self.add_route('/api/:collection/:id', action='update',
                       conditions={'method': ['PUT']})
        self.add_route('/api/:collection/:id', action='method_error',
                       allowed='GET, DELETE, PUT')

    def simple_response(self, status, headers=None, body=None):
        """Send a simple text/plain response to the client."""
        statusline = '%s %s' % (status, http.responses[status])
        if headers is None:
            headers = []
        if body is None:
            body = http.responses[status]
        headers.append(('Date', formatdate()))
        headers.append(('Server', '%s/%s' % (rest.name, rest.version)))
        headers.append(('Content-Type', 'text/plain'))
        headers.append(('Content-Length', str(len(body))))
        self.start_response(statusline, headers)
        return body

    def __iter__(self):
        """Create the response. We always return just one chunk of data."""
        try:
            result = self.respond()
        except Error, e:
            self.logger.debug('Error response: %s' % e.status)
            yield self.simple_response(e.status, e.headers, e.body)
        except Exception, e:
            self.logger.debug('Unknown exception: %s' % type(e))
            tb = getattr(e, 'traceback', traceback.format_exc())
            self.logger.debug(tb)
            yield self.simple_response(http.INTERNAL_SERVER_ERROR)
        else:
            yield result

    def respond(self):
        """Respond to a request."""
        request = Request(self.environ, self.mapper)
        response = Response(self.environ, self.mapper)
        self.logger.debug('New request: %s %s' % (request.method, request.uri))
        match = self.mapper.match(request.path)
        if not match:
            raise Error, http.NOT_FOUND
        request.match = match
        collection = self.collections.get(match['collection'])
        if not collection or not hasattr(collection, match['action']):
            raise Error, http.NOT_FOUND
        input = request.read()
        input = self.filter_input(input, request, response)
        collection.request = request
        collection.response = response
        method = getattr(collection, match['action'])
        kwargs = request.args.copy()
        for key in match:
            if key not in ('controller', 'collection', 'action'):
                kwargs[key] = match[key]
        if input:
            kwargs['input'] = input
        try:
            output = method(**kwargs)
        except Exception, e:
            self.handle_exception(e, request, response)
        output = self.filter_output(output, request, response)
        self.logger.debug('Response: %s (%s; %d bytes)' %
                     (response.status, response.header('Content-Type'),
                      len(output)))
        status = '%s %s' % (response.status, http.responses[response.status])
        self.start_response(status, response.headers)
        return output
