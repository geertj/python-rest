#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from wsgiref.simple_server import (WSGIServer, WSGIRequestHandler,
                                   make_server as _make_server)


class RestServer(WSGIServer):
    """REST HTTP server."""

    def __init__(self, address, handler_class):
        WSGIServer.__init__(self, address, handler_class)
        # Update address if we are listening on a ephemeral port.
        self.address = self.socket.getsockname()

    def shutdown(self):
        self.application.shutdown()
        WSGIServer.shutdown(self)


class RestRequestHandler(WSGIRequestHandler):

    def address_string(self):
        # Do not resolve DNS name of the peer during a request.
        # This can lead to big timeouts.
        return self.client_address[0]

    def log_message(self, format, *args):
        # No logging to standard output
        pass


def make_server(host, port, app):
    return _make_server(host, port, app, RestServer, RestRequestHandler)
