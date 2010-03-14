#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from rest.validator import Validator, ValidationError
from nose.tools import assert_raises


class TestValidator(object):

    def test_simple(self):
        v = Validator()
        v.rule('lname <=> rname')
        left = { 'lname': 'value' }
        right = v.validate(left)
        assert right == { 'rname': 'value' }

    def test_transform(self):
        v = Validator()
        v.rule('int(name) <=> name')
        left = { 'name': '10' }
        right = v.validate(left)
        assert right == { 'name': 10 }

    def test_recursive_transform(self):
        v = Validator()
        v.rule('str(int(name)) <=> name')
        left = { 'name': '10' }
        right = v.validate(left)
        assert right == { 'name': '10' }

    def test_optional_rule(self):
        v = Validator()
        v.rule('name => name')
        right = v.validate({})
        assert right == {}

    def test_mandatory_rule(self):
        v = Validator()
        v.rule('name => name *')
        assert_raises(ValidationError, v.validate, {})

    def test_reverse(self):
        v = Validator()
        v.rule('lname <=> rname')
        right = { 'rname': '10' }
        left = v.reverse(right)
        assert left == { 'lname': '10' }

    def test_reverse_transform(self):
        v = Validator()
        v.rule('lname <=> int(rname)')
        right = { 'rname': '10' }
        left = v.reverse(right)
        assert left == { 'lname': 10 }
