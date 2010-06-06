#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from rest.api import request

def issequence(seq):
    return isinstance(seq, tuple) or isinstance(seq, list)


def make_absolute(relurl):
    url = 'https://' if request.secure else 'http://'
    url += request.server
    if request.secure and request.port != 443 or \
            not request.secure and request.port != 80:
        url += ':%s' % request.port
    url += relurl
    return url
