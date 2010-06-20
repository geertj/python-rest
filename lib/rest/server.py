#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import re
import sys
import os.path
from optparse import OptionParser
from wsgiref.simple_server import (WSGIServer, WSGIRequestHandler,
                                   make_server as _make_server)

from rest.util import setup_logging, import_module

re_listen = re.compile('([-a-z0-9.]+):([0-9]+)', re.I)
re_module = re.compile('([a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]+)*)'
                       ':([a-z_][a-z0-9_]+)', re.I)


class RESTServer(WSGIServer):
    """REST HTTP server."""

    def __init__(self, address, handler_class):
        WSGIServer.__init__(self, address, handler_class)
        # Update address if we are listening on a ephemeral port.
        self.address = self.socket.getsockname()

    def shutdown(self):
        self.application.shutdown()
        WSGIServer.shutdown(self)


class RESTRequestHandler(WSGIRequestHandler):

    def address_string(self):
        # Do not resolve DNS name of the peer during a request.
        # This can lead to big timeouts.
        return self.client_address[0]

    def log_message(self, format, *args):
        # No logging to standard output
        pass


def make_server(host, port, app):
    return _make_server(host, port, app, RESTServer, RESTRequestHandler)


def program_name():
    name = sys.argv[0]
    name = name.replace('-script.py', '')
    dummy, name = os.path.split(name)
    return name


def main():
    """Command-line integration. Start up the API based on the built-in
    wsgiref web server."""
    parser = OptionParser(prog=program_name())
    parser.add_option('-l', '--listen', dest='listen',
                      help='listen on interface:port')
    parser.add_option('-m', '--module', dest='module',
                      help='use application module:classname')
    parser.add_option('-d', '--debug', action='store_true')
    parser.set_default('listen', 'localhost:8080')
    parser.set_default('debug', False)
    parser.set_default('module', None)
    opts, args = parser.parse_args()
    if not opts.module:
        parser.error('you need to specify --module')
    mobj = re_module.match(opts.module)
    if not mobj:
        parser.error('specify --module as module:classname')
    modname = mobj.group(1)
    classname = mobj.group(2)
    module = import_module(modname)
    if module is None:
        parser.error('could not load module %s' % modname)
    if not hasattr(module, classname):
        parser.error('could not load class %s from module' % classname)
    app = getattr(module, classname)
    mobj = re_listen.match(opts.listen)
    if not mobj:
        parser.error('specify --listen as host:port')
    address = mobj.group(1)
    port = int(mobj.group(2))
    setup_logging(opts.debug)
    server = make_server(address, port, app)
    print 'Listening on %s:%s' % (address, port)
    print 'Press CTRL-C to quit'
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
