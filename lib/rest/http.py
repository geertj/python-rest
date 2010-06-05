#
# This file is part of RHEVM-API. RHEVM-API is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# RHEVM-API is copyright (c) 2010 by the RHEVM-API authors. See the file
# "AUTHORS" for a complete overview.

import itertools
from collections import namedtuple
from httplib import responses as reasons
from httplib import HTTP_PORT as PORT, HTTPS_PORT as SSL_PORT
from rfc822 import formatdate as format_date


# Export HTTP status codes
for key in reasons:
    value = reasons[key]
    name = value.upper().replace(' ', '_').replace('-', '_')
    globals()[name] = key


def _parse_header_options(options):
    """Parse header options. Return a list of (key, value) tuples."""
    (s_sync, s_read_key, s_start_value, s_read_value,
     s_read_quoted_value, s_read_quoted_value_escape) = range(6)
    state = namedtuple('state', ('state', 'key', 'value'))
    state.state = s_sync
    result = []
    for ch in itertools.chain(' ', options, ';'):
        if state.state == s_sync:
            if ch not in ' ;':
                state.state = s_read_key
                state.key = ch
        elif state.state == s_read_key:
            if ch == '=':
                state.state = s_start_value
            else:
                state.key += ch
        elif state.state == s_start_value:
            if ch == '"':
                state.state = s_read_quoted_value
                state.value = ''
            else:
                state.state = s_read_value
                state.value = ch
        elif state.state == s_read_value:
            if ch in ' ;':
                result.append((state.key, state.value))
                state.state = s_sync
            else:
                state.value += ch
        elif state.state == s_read_quoted_value:
            if ch == '\\':
                state.state = s_read_quoted_value_escape
            elif ch == '"':
                result.append((state.key, state.value))
                state.state = s_sync
            else:
                state.value += ch
        elif state.state == s_read_quoted_value_escape:
            state.value += ch
            state.state = s_read_quoted_value
    if state.state != s_sync:
        raise ValueError, 'Illegal header options value.'
    return result


def parse_content_type(header):
    """Parse a "Content-Type" header. Return a tuple of (type, subtype,
    options)."""
    # RFC2045, RFC822
    s_sync, s_read_type, s_read_subtype, s_read_options = range(4)
    state = s_sync
    type = subtype = options = ''
    for ch in header:
        if state == s_sync:
            if ch != ' ':
                type = ch
                state = s_read_type
        elif state == s_read_type:
            if ch == '/':
                state = s_read_subtype
            else:
                type += ch
        elif state == s_read_subtype:
            if ch == ';':
                state = s_read_options
            else:
                subtype += ch
        elif state == s_read_options:
            options += ch
    if state not in (s_read_subtype, s_read_options):
        raise ValueError, 'Illegal Content-Type header.'
    options = _parse_header_options(options)
    return (type, subtype, options)


def parse_accept(accept):
    """Parse an "Accept" header and return a list of (type, params) in
    descending order."""
    result = []
    parts = accept.split(',')
    try:
        for index,part in enumerate(parts):
            subparts = part.split(';')
            fulltype = subparts[0].strip()
            type, subtype = fulltype.split('/')
            params = {}
            for subpart in subparts[1:]:
                key, value = subpart.split('=')
                params[key.strip()] = value.strip()
            sortkey = (-int(type == '*'), -int(subtype == '*'),
                       -float(params.get('q', '1')), index)
            result.append((sortkey, fulltype, params))
    except (ValueError, TypeError):
        raise ValueError, 'Illegal "Accept" header.'
    result.sort()
    result = [ (res[1], res[2]) for res in result]
    return result
