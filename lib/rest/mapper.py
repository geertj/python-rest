#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that
# is distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the
# file "AUTHORS" for a complete overview.

"""
This module contains trivial re-implementation of Python Routes. It is
not near as feature complete but it small and it removes an external
dependency.
"""

import re
from string import Template


class Route(object):

    _re_var = re.compile(':([a-z][a-z0-9_]*)|{([a-z][a-z0-9_]*)}', re.I)

    def __init__(self, path, method=None, **kwargs):
        self.path = path
        self.method = method
        self.kwargs = kwargs
        self.varnames = []
        self.pattern = '^%s$' % self._re_var.sub(self._replace_var_names,
                                                 self.path)
        self.regex = re.compile(self.pattern)
        self.template = Template(self._re_var.sub(self._template_var_names,
                                                  self.path))

    def _replace_var_names(self, mobj):
        name = mobj.group(1) or mobj.group(2)
        self.varnames.append(name)
        return '(?P<%s>[^/]+)' % name

    def _template_var_names(self, mobj):
        name = mobj.group(1) or mobj.group(2)
        return '$%s' % name
        
    def _match(self, url, method=None):
        mobj = self.regex.match(url)
        if not mobj:
            return
        if method and self.method and method != self.method:
            return
        match = mobj.groupdict().copy()
        match.update(self.kwargs)
        return match

    def _url_for(self, **kwargs):
        args = set(kwargs)
        for name in self.varnames:
            if name not in kwargs:
                return
            args.remove(name)
        for arg in self.kwargs:
            if self.kwargs[arg] != kwargs.get(arg):
                return
            args.remove(arg)
        if args:
            return
        url = self.template.substitute(kwargs)
        return url


class Mapper(object):

    def __init__(self):
        self.routes = []

    def connect(self, path, method=None, **kwargs):
        route = Route(path, method, **kwargs)
        self.routes.append(route)

    def match(self, url, method=None):
        for route in self.routes:
            match = route._match(url, method)
            if match:
                return match

    def url_for(self, **kwargs):
        for route in self.routes:
            url = route._url_for(**kwargs)
            if url:
                return url

    def methods_for(self, url):
        methods = []
        for route in self.routes:
            match = route._match(url, method=None)
            if match and route.method:
                methods.append(route.method)
        return methods
