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
from email.utils import formatdate as format_date
try:
    from urllib.parse import parse_qs
except ImportError:
    from cgi import parse_qs


# Export HTTP status codes
for key in reasons:
    value = reasons[key]
    name = value.upper().replace(' ', '_').replace('-', '_')
    globals()[name] = key


def _parse_parameterized_list(header):
    """Parse a "parameterized list" HTTP header into a list of
    (header, options) tuples, with options a list of (name, value) tuples.
    
    This function can be used to parse parameters like "Accept,"
    "Accept-Encoding," and "Content-Type," that have the following general
    format:

      Header Value 1; param1=value1, Header Value 2; param2=value2
    """
    (s_sync_header, s_read_header, s_sync_parameter, s_read_parameter,
     s_sync_value, s_read_value, s_read_quoted_value,
     s_read_quoted_value_escape, s_sync_header_or_parameter) = range(9)
    state = namedtuple('state', ('state', 'header', 'parameter', 'value', 'options'))
    state.state = s_sync_header
    result = []
    for ch in itertools.chain(' ', header, ','):
        if state.state == s_sync_header:
            if ch != ' ':
                state.state = s_read_header
                state.header = ch
                state.options = []
        elif state.state == s_read_header:
            if ch == ',':
                result.append((state.header, state.options))
                state.state = s_sync_header
            elif ch == ';':
                state.state = s_sync_parameter
            else:
                state.header += ch
        elif state.state == s_sync_parameter:
            if ch != ' ':
                state.state = s_read_parameter
                state.parameter = ch
        elif state.state == s_read_parameter:
            if ch == '=':
                state.state = s_sync_value
            else:
                state.parameter += ch
        elif state.state == s_sync_value:
            if ch == '"':
                state.state = s_read_quoted_value
                state.value = ''
            elif ch != ' ':
                state.state = s_read_value
                state.value = ch
        elif state.state == s_read_value:
            if ch == ',':
                state.options.append((state.parameter, state.value))
                result.append((state.header, state.options))
                state.state = s_sync_header
            elif ch == ';':
                state.options.append((state.parameter, state.value))
                state.state = s_sync_parameter
            else:
                state.value += ch
        elif state.state == s_read_quoted_value:
            if ch == '\\':
                state.state = s_read_quoted_value_escape
            elif ch == '"':
                state.options.append((state.parameter, state.value))
                state.state = s_sync_header_or_parameter
            else:
                state.value += ch
        elif state.state == s_read_quoted_value_escape:
            state.value += ch
            state.state = s_read_quoted_value
        elif state.state == s_sync_header_or_parameter:
            if ch == ',':
                result.append((state.header, state.options))
                state.state = s_sync_header
            elif ch == ';':
                state.state = s_sync_parameter
            else:
                raise ValueError, 'Could not parse HTTP header.'
    if state.state != s_sync_header:
        raise ValueError, 'Could not parse HTTP header.'
    return result


def parse_content_type(header):
    """Parse a "Content-Type" header. Return a tuple of (type, subtype,
    options)."""
    parsed = _parse_parameterized_list(header)
    if len(parsed) != 1:
        raise ValueError, 'Could not parse Content-Type header'
    header, options = parsed[0]
    try:
        type, subtype = header.split('/')
    except ValueError:
        raise ValueError, 'Could not parse Content-Type header'
    options = dict(((key.lower(), value) for key,value in options))
    return (type.lower(), subtype.lower(), options)


def select_content_type(ctypes, accept_header):
    """Select the most suitable content type from a list of supported content
    types, based on the value of an "Accept" header.
    """
    # See RFC2616, section 14.1.
    parsed = _parse_parameterized_list(accept_header)
    accept_header = []
    for header,options in parsed:
        try:
            type, subtype = header.split('/')
        except ValueError:
            raise ValueError, 'Could not parse Content-Type header'
        options = dict(((key.lower(), value) for key,value in options))
        accept_header.append((type.lower(), subtype.lower(), options))
    candidates = []
    for ix,ctype in enumerate(ctypes):
        supported = parse_content_type(ctype)
        matches = []
        for accepted in accept_header:
            if supported[0] != accepted[0] and accepted[0] != '*':
                continue
            if supported[1] != accepted[1] and accepted[1] != '*':
                continue
            if accepted[2].has_key('q'):
                supported[2]['q'] = accepted[2]['q']  # Ignore 'q'
            if supported[2] != accepted[2] and accepted[2]:
                continue
            if accepted[0] == '*':
                precedence = 0
            elif accepted[1] == '*':
                precedence = 1
            else:
                precedence = 2 + len(accepted[2])
            qfactor = float(accepted[2].get('q', '1'))
            matches.append((precedence, qfactor))
        if not matches:
            continue
        matches.sort()
        candidates.append((matches[-1][1], -ix, ctype))
    if not candidates:
        return
    candidates.sort()
    return candidates[-1][2]
            

def select_charset(charsets, accept_header):
    """Select the most suitable charset to use from a list of supported
    charset, based on the value of an "Accept-Charset" header.
    """
    # See RFC2616, section 14.2.
    parsed = _parse_parameterized_list(accept_header)
    accept_header = []
    for header,options in parsed:
        options = dict(((key.lower(), value) for key,value in options))
        accept_header.append((header.lower(), options))
    non_wildcard_charsets = set()
    for charset,options in accept_header:
        if charset != '*':
            non_wildcard_charsets.add(charset)
    candidates = []
    for ix,charset in enumerate(charsets):
        for accept,options in accept_header:
            if charset == accept or \
                    (accept == '*' and charset not in non_wildcard_charsets):
                qfactor = float(options.get('q', '1'))
                candidates.append((qfactor, -ix, charset))
                break
        else:
            if charset == 'iso-8859-1':
                candidates.append((1.0, -ix, charset))
    if not candidates:
        return
    candidates.sort()
    return candidates[-1][2]
