#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from rest import api
from rest.entity import *
from rest.request import Request
from rest.response import Response
from rest.collection import Collection
from nose.tools import assert_raises


class BookCollection(Collection):

    name = 'books'
    parse_hints = """
        /book/reviews: sequence
        """


class TestParseEntity(object):

    environ = {
        'SCRIPT_NAME': '/api/books',
        'PATH_INFO': '',
        'QUERY_STRING': '',
        'REQUEST_METHOD': 'POST',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '80',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'CONTENT_TYPE': 'text/xml',
    }

    testdata = [
        (
            """<?xml version="1.0" ?>
               <book><title>Book Title</title><year>2010</year></book>
            """,
            """!book
               title: Book Title
               year: !!str 2010
            """,
            { '!type': 'book', 'title': 'Book Title', 'year': '2010' }
        ),
        (
            """<?xml version="1.0" ?>
               <book>
               <title>Book Title</title><year>2010</year>
               <reviews><review><comment>Great book</comment></review></reviews>
               </book>
            """,
            """!book
               title: Book Title
               year: !!str 2010
               reviews:
                 - !review
                   comment: Great book
                """,
            { '!type': 'book', 'title': 'Book Title', 'year': '2010',
                'reviews': [ { '!type': 'review', 'comment': 'Great book' } ] }
        ),
        (
            """<?xml version="1.0" ?>
               <book>
                 <title>Book Title</title><year>2010</year>
                 <reviews><review><comment>Great book</comment></review>
                   <review><comment>Very nice indeed</comment></review></reviews>
               </book>
            """,
            """!book
               title: Book Title
               year: !!str 2010
               reviews:
                 - !review
                   comment: Great book
                 - !review
                   comment: Very nice indeed
                """,
            { '!type': 'book', 'title': 'Book Title', 'year': '2010',
                'reviews': [ { '!type': 'review', 'comment': 'Great book' },
                             { '!type': 'review', 'comment': 'Very nice indeed' } ] }
        ),
        (
            """<?xml version="1.0" ?>
               <book>
                 <title>Book Title</title><year>2010</year>
                 <review><comment>Great book</comment></review>
               </book>
            """,
            """!book
               title: Book Title
               year: !!str 2010
               review: !review
                 comment: Great book
            """,
            { '!type': 'book', 'year': '2010', 'title': 'Book Title', 'review':
                    { '!type': 'review', 'comment': 'Great book' } }
        )
    ]



    def setup(self):
        request = Request(self.environ)
        api.request._register(request)
        response = Response(self.environ)
        api.response._register(response)
        collection = BookCollection()
        api.collection._register(collection)

    def test_round_trips_xml(self):
        parser = ParseEntity()
        formatter = FormatEntity()
        for xml,yaml,resource in self.testdata:
            api.request.set_header('Accept', 'text/xml')
            api.request.set_header('Content-Type', 'text/xml')
            assert parser.filter(xml) == resource
            output = formatter.filter(resource)
            assert parser.filter(output) == resource

    def test_round_trips_yaml(self):
        parser = ParseEntity()
        formatter = FormatEntity()
        for xml,yaml,resource in self.testdata:
            api.request.set_header('Accept', 'text/yaml')
            api.request.set_header('Content-Type', 'text/yaml')
            assert parser.filter(yaml) == resource
            output = formatter.filter(resource)
            assert parser.filter(output) == resource

    def test_round_trips_list_xml(self):
        parser = ParseEntity()
        formatter = FormatEntity()
        for xml,yml,resource in self.testdata:
            api.request.set_header('Accept', 'text/xml')
            api.request.set_header('Content-Type', 'text/xml')
            output = formatter.filter([resource])
            root = etree.fromstring(output)
            assert root.tag == api.collection.name
            output = etree.tostring(root[0])
            parsed = parser.filter(output)
            assert parsed == resource

    def test_round_trips_list_yaml(self):
        parser = ParseEntity()
        formatter = FormatEntity()
        for xml,yml,resource in self.testdata:
            api.request.set_header('Accept', 'text/yaml')
            api.request.set_header('Content-Type', 'text/yaml')
            output = formatter.filter([resource])
            output = output.replace('\n- ', '\n  ')  # hack, list -> entry
            parsed = parser.filter(output)
            assert parsed == resource
