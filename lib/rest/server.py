#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from wsgiref.simple_server import WSGIServer, make_server as _make_server


class PatchedWSGIServer(WSGIServer):
    """A hacked up WSGI server that provides a .shutdown() method also in
    Python 2.5. The standard shutdown() method appeared in 2.6."""

    def __init__(self, address, handler_class):
        WSGIServer.__init__(self, address, handler_class)
        self._stopped = False
        self.socket.settimeout(0.5)

    def serve_forever(self):
        while not self._stopped:
            self.handle_request()

    def shutdown(self):
        self._stopped = True


def make_server(host, port, app):
    if hasattr(WSGIServer, 'shutdown'):
        server_class = WSGIServer
    else:
        server_class = PatchedWSGIServer
    return _make_server(host, port, app, server_class)
