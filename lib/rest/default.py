#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from rest.filter import *


def setup(app):
    app.add_route('/api/:collection', method='GET', action='list')
    app.add_route('/api/:collection', method='POST', action='create')
    app.add_route('/api/:collection/:id', method='DELETE', action='delete')
    app.add_route('/api/:collection/:id', method='GET', action='show')
    app.add_route('/api/:collection/:id', method='PUT', action='update')
    app.add_route('/api/:collection', action='_method_not_allowed')
    app.add_route('/api/:collection/:id', action='_method_not_allowed')

    app.add_input_filter(CheckMethodAllowed())
    app.add_output_filter(HandleNoneOutput(), priority=HIGHEST)
    app.add_output_filter(ConvertUnicodeToBytes(), priority=LOWEST)
    app.add_exception_handler(HandleCommonExceptions())

    app.add_input_filter(AssertNoInput(), action='show')
    app.add_output_filter(NotFoundIfNoResponse(), action='show')
    app.add_input_filter(AssertNoInput(), action='list')
    app.add_input_filter(AssertNoInput(), action='delete')
    app.add_input_filter(RequireInput(), action='create')
    app.add_output_filter(SetLocationHeader(), action='create')
    app.add_input_filter(RequireInput(), action='update')
