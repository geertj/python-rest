#
# This file is part of RHEVM-API. RHEVM-API is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# RHEVM-API is copyright (c) 2010 by the RHEVM-API authors. See the file
# "AUTHORS" for a complete overview.

from httplib import responses as reasons
from httplib import HTTP_PORT as PORT, HTTPS_PORT as SSL_PORT
from rfc822 import formatdate as format_date


# Export HTTP status codes
for key in reasons:
    value = reasons[key]
    name = value.upper().replace(' ', '_').replace('-', '_')
    globals()[name] = key


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



