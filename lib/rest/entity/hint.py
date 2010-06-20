#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import re


class Hints(object):

    def __init__(self):
        self.hints = []

    def _parse_hints(self, hints):
        # XXX: this probaly needs a real parser.
        result = []
        lines = hints.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                path, hints = line.split(':')
            except ValueError:
                raise ValueError, 'Illegal entity hint.'
            hresult = {}
            hints = [ hint.split('=') for hint in hints.split(',') ]
            for hint in hints:
                if len(hint) == 1:
                    hresult[hint[0].strip()] = True
                else:
                    hresult[hint[0].strip()] = hint[1].strip()
            result.append((path.strip(), hresult))
        return result

    def _create_regex(self, path):
        regex = path.replace('[', r'\[',).replace(']', r'\]') \
                    .replace('*', '[^/]+')
        if regex.startswith('/'):
            regex = '^%s$' % regex
        else:
            regex = '^.*%s$' % regex
        regex = re.compile(regex)
        return regex

    def add_hints(self, hints):
        hints = self._parse_hints(hints)
        for path,hints in hints:
            regex = self._create_regex(path)
            self.hints.append((regex, hints))

    def get(self, path):
        if isinstance(path, list) or isinstance(path, tuple):
            path = '/' + '/'.join(path)
        for regex,hints in self.hints:
            if regex.match(path):
                return hints
        return {}
