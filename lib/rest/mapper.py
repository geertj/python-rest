#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

"""
This file is a trivial re-implementation of Python Routes. It is not near as
feature complete but it small and it reduces an external dependency.
"""

import re
from string import Template


class Route(object):

    path = None
    methods = ['GET', 'POST', 'PUT', 'DELETE']
    args = {}

    _re_var = re.compile(':([a-z][a-z0-9_]+)|{([a-z][a-z0-9_]+)}', re.I)

    def __init__(self, path=None, methods=None, **kwargs):
        if path is not None:
            self.path = path
        if methods is not None:
            self.methods = methods
        if kwargs:
            self.args = self.args.copy()
            self.args.update(kwargs)
        self.varnames = []
        self.pattern = '^%s$' % self._re_var.sub(self._replace_var_names,
                                                 self.path)
        self.regex = re.compile(self.pattern)
        self.template = Template(self._re_var.sub('$\\1', self.path))

    def _replace_var_names(self, mobj):
        name = mobj.group(1) or mobj.group(2)
        self.varnames.append(name)
        return '(?P<%s>[^/]+)' % name

    def _match(self, **kwargs):
        for name in self.varnames:
            if name not in kwargs:
                return False
        for arg in self.args:
            if self.args[arg] != kwargs.get(arg):
                return False
        return True


class Mapper(object):

    def __init__(self):
        self.routes = []

    def connect(self, route):
        self.routes.append(route)

    def match(self, url, method=None):
        for route in self.routes:
            mobj = route.regex.match(url)
            if not mobj:
                continue
            if method and method not in route.methods:
                continue
            ret = mobj.groupdict().copy()
            ret.update(route.args)
            return ret

    def url_for(self, **kwargs):
        for route in self.routes:
            if route._match(**kwargs):
                url = route.template.substitute(kwargs)
                return url
