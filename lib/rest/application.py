#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import sys
import logging
import traceback

import rest
import rest.api

from rest.request import Request
from rest.response import Response
from rest.error import Error
from rest.mapper import Mapper
from rest import http


class Application(object):
    """A mini framework for creating RESTful APIs."""

    def __init__(self, environ, start_response):
        """Constructor."""
        self.environ = environ
        self.start_response = start_response
        self.collections = {}
        self.mapper = Mapper()
        self.input_filters = {}
        self.output_filters = {}
        self.exception_handlers = {}
        self.serial = 0
        self.logger = logging.getLogger('rest')
        self.load_modules()
        self.setup_collections()
        self.setup_routes()
        self.setup_filters()

    def _serial(self):
        """INTERNAL: return a monotonically increasing counter."""
        serial = self.serial
        self.serial += 1
        return serial

    def add_collection(self, collection):
        """Add a single collection."""
        self.collections[collection.name] = collection

    def setup_collections(self):
        """Implement this method in a subclass to add collections."""

    def add_route(self, *args, **kwargs):
        """Add a route."""
        self.mapper.connect(*args, **kwargs)

    def setup_routes(self):
        """Implement this method in a subclass to add routes."""

    def add_input_filter(self, filter, collection=None, action=None, priority=50):
        """Add an input filter."""
        if isinstance(action, tuple) or isinstance(action, list):
            for act in action:
                self.add_input_filter(filter, collection, act, priority)
            return
        key = (collection, action)
        if key not in self.input_filters:
            self.input_filters[key] = []
        self.input_filters[key].append((priority, self._serial(), filter))

    def add_output_filter(self, filter, collection=None, action=None, priority=50):
        """Add an output filter."""
        if isinstance(action, tuple) or isinstance(action, list):
            for act in action:
                self.add_output_filter(filter, collection, act, priority)
            return
        key = (collection, action)
        if key not in self.output_filters:
            self.output_filters[key] = []
        self.output_filters[key].append((priority, self._serial(), filter))

    def add_exception_handler(self, handler, collection=None, action=None, priority=50):
        """Add an exception handler."""
        if isinstance(action, tuple) or isinstance(action, list):
            for act in action:
                self.add_exception_handler(handler, collection, act, priority)
            return
        key = (collection, action)
        if key not in self.exception_handlers:
            self.exception_handlers[key] = []
        self.exception_handlers[key].append((priority, self._serial(), handler))

    def setup_filters(self):
        """Implement this method in a subclass to add filters."""

    def load_module(self, module):
        """Load all collections, routes, input filters, output filters and
        exception handlers from a module."""
        __import__(module)
        try:
            setup_module = getattr(sys.modules[module], 'setup_module')
        except AttributeError:
            return
        setup_module(self)

    def load_modules(self):
        """Implement this method in a subclass to load modules."""
        self.load_module('rest.defcfg')

    def filter_input(self, collection, action, input):
        """Filter input."""
        filters = self.input_filters.get((collection, action), [])
        filters += self.input_filters.get((None, action), [])
        filters += self.input_filters.get((collection, None), [])
        filters += self.input_filters.get((None, None), [])
        filters.sort(lambda x,y: cmp(x[0:2], y[0:2]))
        for prio, serial, filter in filters:
            input = filter.filter(input)
        return input

    def filter_output(self, collection, action, output):
        """Filter input."""
        filters = self.output_filters.get((collection, action), [])
        filters += self.output_filters.get((None, action), [])
        filters += self.output_filters.get((collection, None), [])
        filters += self.output_filters.get((None, None), [])
        filters.sort(lambda x,y: cmp(x[0:2], y[0:2]))
        for prio, serial, filter in filters:
            output = filter.filter(output)
        return output

    def handle_exception(self, collection, action, exception):
        """Handle an exception."""
        handlers = self.exception_handlers.get((collection, action), [])
        handlers += self.exception_handlers.get((None, action), [])
        handlers += self.exception_handlers.get((collection, None), [])
        handlers += self.exception_handlers.get((None, None), [])
        handlers.sort(lambda x,y: cmp(x[0:2], y[0:2]))
        for prio, serial, handler in handlers:
            exception = handler.handle(exception)
        return exception

    def simple_response(self, status, headers=None, body=None):
        """Send a simple text/plain response to the client."""
        statusline = '%s %s' % (status, http.reasons[status])
        if headers is None:
            headers = []
        if body is None:
            body = http.reasons[status]
        headers.append(('Date', http.format_date()))
        headers.append(('Server', '%s/%s' % (rest.name, rest.version)))
        headers.append(('Content-Type', 'text/plain'))
        headers.append(('Content-Length', str(len(body))))
        self.start_response(statusline, headers)
        return body

    def register_globals(self, collection, request, response):
        """Register global objects."""
        rest.api.request._register(request)
        rest.api.response._register(response)
        rest.api.collection._register(collection)
        rest.api.mapper._register(self.mapper)
        rest.api.application._register(self)

    def release_globals(self):
        """Release globals."""
        rest.api.request._release()
        rest.api.response._release()
        rest.api.collection._release()
        rest.api.mapper._release()
        rest.api.application._release()

    def __iter__(self):
        """Create the response. We always return just one chunk of data."""
        try:
            result = self.respond()
        except Error, e:
            self.logger.debug('Error response: %s' % e.status)
            self.logger.debug('Reason: %s' % e.reason)
            yield self.simple_response(e.status, e.headers, e.body)
        except Exception, e:
            self.logger.debug('Unknown exception: %s' % type(e))
            tb = getattr(e, 'traceback', traceback.format_exc())
            self.logger.debug('Traceback: %s' % tb)
            yield self.simple_response(http.INTERNAL_SERVER_ERROR)
        else:
            yield result

    def respond(self):
        """Respond to a request."""
        request = Request(self.environ)
        response = Response(self.environ)
        self.logger.debug('New request: %s %s' % (request.method, request.uri))
        m = self.mapper.match(request.path, request.method)
        if not m:
            raise Error(http.NOT_FOUND, reason='URL unmapped')
        self.logger.debug('URL mapped to %s:%s' % (m['collection'], m['action']))
        request.match = m
        collection = self.collections.get(m['collection'])
        if not collection or not hasattr(collection, m['action']):
            raise Error(http.NOT_FOUND, reason='Collection/action not found')
        method = getattr(collection, m['action'])
        kwargs = request.args.copy()
        for key in m:
            if key not in ('collection', 'action'):
                kwargs[key] = m[key]
        input = request.read()
        self.logger.debug('Read %d bytes of input' % len(input))
        self.register_globals(collection, request, response)
        try:
            self.logger.debug('Running input filters')
            input = self.filter_input(m['collection'], m['action'], input)
            if input:
                kwargs['input'] = input
            output = None
            collection.setup()
            try:
                output = method(**kwargs)
            except Exception, exception:
                self.logger.debug('Exception occurred, running handlers.')
                exception = self.handle_exception(m['collection'], m['action'],
                                                  exception)
                if exception:
                    raise exception
            finally:
                collection.close()
            self.logger.debug('Running output filters')
            output = self.filter_output(m['collection'], m['action'], output)
        finally:
            self.release_globals()
        self.logger.debug('Response: %s (%s; %d bytes)' %
                     (response.status, response.header('Content-Type'),
                      len(output)))
        status = '%s %s' % (response.status, http.reasons[response.status])
        self.start_response(status, response.headers)
        return output
