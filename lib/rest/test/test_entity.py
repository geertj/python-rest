#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

from copy import deepcopy

from rest import api
from rest.entity import *
from rest.request import Request
from rest.response import Response
from rest.collection import Collection
from rest.application import Application
from rest.entity.parse import ParserManager
from rest.entity.format import FormatterManager
from rest.entity.transform import Transformer
from rest.entity.xml import XMLParser, XMLFormatter
from rest.entity.yaml import YAMLFormatter, YAMLParser
from rest.entity.json import JSONFormatter, JSONParser
from nose.tools import assert_raises


class BookCollection(Collection):

    name = 'books'
    contains = 'book'
    parse_hints = """
        review: type=review
        reviews: sequence, type=review
        """
    entity_transform = """
        $!type.title() <=> $!type.lower()
        $title <=> $Title
        $year <=> $Year
        $author <=> $Author
        $review <=> $Review
        $reviews <=> $Reviews
        """


class ReviewCollection(Collection):

    name = 'reviews'
    contains = 'review'
    entity_transform = """
        $!type.title() <=> $!type.lower()
        $comment <=> $Comment
        """


class BookApplication(Application):
    
    def setup_collections(self):
        self.add_collection(BookCollection())
        self.add_collection(ReviewCollection())


class TestEntity(object):

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
               <book>
                 <title>Book Title</title>
                 <year>2010</year>
                 <author>Book Author</author>
               </book>
            """,
            """!book
               title: Book Title
               year: !!str 2010
               author: Book Author
            """,
            """{ "title": "Book Title", "year": "2010",
                 "author": "Book Author" }
            """,
            { '!type': 'Book', 'Title': 'Book Title', 'Year': '2010',
              'Author': 'Book Author' }
        ),
        (
            """<?xml version="1.0" ?>
               <book>
                 <title>Book Title</title>
                 <year>2010</year>
                 <author>Book Author</author>
                 <reviews>
                   <review>
                     <comment>Great book</comment>
                   </review>
                 </reviews>
               </book>
            """,
            """!book
               title: Book Title
               year: !!str 2010
               author: Book Author
               reviews:
                 - !review
                   comment: Great book
                """,
            """{ "book": "Book Title", "year": "2010",
                 "author": "Book Author", "title": "Book Title",
                 "reviews": [ { "comment": "Great book" }] }
            """,
            { '!type': 'Book', 'Title': 'Book Title', 'Year': '2010',
              'Author': 'Book Author',
              'Reviews': [ { '!type': 'Review', 'Comment': 'Great book' } ] }
        ),
        (
            """<?xml version="1.0" ?>
               <book>
                 <title>Book Title</title>
                 <year>2010</year>
                 <author>Book Author</author>
                 <reviews>
                   <review>
                     <comment>Great book</comment>
                   </review>
                   <review>
                     <comment>Very nice indeed</comment>
                   </review>
                 </reviews>
               </book>
            """,
            """!book
               title: Book Title
               year: !!str 2010
               author: Book Author
               reviews:
                 - !review
                   comment: Great book
                 - !review
                   comment: Very nice indeed
            """,
            """{ "book": "Book Title", "year": "2010",
                 "author": "Book Author", "title": "Book Title",
                 "reviews": [ { "comment": "Great book" },
                              { "comment": "Very nice indeed" } ] }
            """,
            { '!type': 'Book', 'Title': 'Book Title',
              'Year': '2010', 'Author': 'Book Author',
                'Reviews': [ { '!type': 'Review', 'Comment': 'Great book' },
                             { '!type': 'Review', 'Comment': 'Very nice indeed' } ] }
        ),
        (
            """<?xml version="1.0" ?>
               <book>
                 <title>Book Title</title>
                 <year>2010</year>
                 <author>Book Author</author>
                 <review>
                   <comment>Great book</comment>
                  </review>
               </book>
            """,
            """!book
               title: Book Title
               year: !!str 2010
               author: Book Author
               review: !review
                 comment: Great book
            """,
            """{ "book": "Book Title", "year": "2010",
                 "author": "Book Author", "title": "Book Title",
                 "review": { "comment": "Great book" } }
            """,
            { '!type': 'Book', 'Year': '2010', 'Title': 'Book Title',
              'Author': 'Book Author', 'Review':
                    { '!type': 'Review', 'Comment': 'Great book' } }
        )
    ]


    def setup(self):
        request = Request(self.environ)
        request.match = { 'action': 'list' }
        api.request._register(request)
        response = Response(self.environ)
        api.response._register(response)
        collection = BookCollection()
        api.collection._register(collection)
        application = BookApplication(self.environ, None)
        api.application._register(application)
        parser = ParserManager()
        parser.add_parser('text/xml', XMLParser())
        parser.add_parser('text/x-yaml', YAMLParser())
        parser.add_parser('application/json', JSONParser())
        self.parser = parser
        formatter = FormatterManager()
        formatter.add_formatter('text/xml', XMLFormatter())
        formatter.add_formatter('text/x-yaml', YAMLFormatter())
        formatter.add_formatter('application/json', JSONFormatter())
        self.formatter = formatter
        self.transformer = Transformer()

    def test_round_trip_xml(self):
        for xml,yaml,json,resource in self.testdata:
            resource = deepcopy(resource)
            api.request.set_header('Accept', 'text/xml')
            api.request.set_header('Content-Type', 'text/xml')
            parsed = self.parser.parse(xml)
            transformed = self.transformer.transform(parsed)
            assert transformed == resource
            reversed = self.transformer.transform(transformed, reverse=True)
            formatted = self.formatter.format(reversed)
            parsed = self.parser.parse(formatted)
            transformed = self.transformer.transform(parsed)
            assert transformed == resource

    def test_round_trip_yaml(self):
        for xml,yaml,json,resource in self.testdata:
            resource = deepcopy(resource)
            api.request.set_header('Accept', 'text/x-yaml')
            api.request.set_header('Content-Type', 'text/x-yaml')
            parsed = self.parser.parse(yaml)
            transformed = self.transformer.transform(parsed)
            assert transformed == resource
            reversed = self.transformer.transform(transformed, reverse=True)
            formatted = self.formatter.format(reversed)
            parsed = self.parser.parse(formatted)
            transformed = self.transformer.transform(parsed)
            assert transformed == resource

    def test_round_trip_json(self):
        for xml,yaml,json,resource in self.testdata:
            resource = deepcopy(resource)
            api.request.set_header('Accept', 'application/json')
            api.request.set_header('Content-Type', 'application/json')
            parsed = self.parser.parse(json)
            transformed = self.transformer.transform(parsed)
            assert transformed == resource
            reversed = self.transformer.transform(transformed, reverse=True)
            formatted = self.formatter.format(reversed)
            parsed = self.parser.parse(formatted)
            transformed = self.transformer.transform(parsed)
            assert transformed == resource

    def test_round_trip_xml_list(self):
        for xml,yaml,json,resource in self.testdata:
            resource = deepcopy(resource)
            api.request.set_header('Accept', 'text/xml')
            api.request.set_header('Content-Type', 'text/xml')
            reversed = self.transformer.transform([resource, resource],
                                                  reverse=True)
            formatted = self.formatter.format(reversed)
            parsed = self.parser.parse(formatted)
            transformed = self.transformer.transform(parsed)
            assert transformed == [resource, resource]

    def test_round_trip_yaml_list(self):
        for xml,yaml,json,resource in self.testdata:
            resource = deepcopy(resource)
            api.request.set_header('Accept', 'text/x-yaml')
            api.request.set_header('Content-Type', 'text/x-yaml')
            reversed = self.transformer.transform([resource, resource],
                                                  reverse=True)
            formatted = self.formatter.format(reversed)
            parsed = self.parser.parse(formatted)
            transformed = self.transformer.transform(parsed)
            assert transformed == [resource, resource]

    def test_round_trip_json_list(self):
        for xml,yaml,json,resource in self.testdata:
            resource = deepcopy(resource)
            api.request.set_header('Accept', 'application/json')
            api.request.set_header('Content-Type', 'application/json')
            reversed = self.transformer.transform([resource, resource],
                                                  reverse=True)
            formatted = self.formatter.format(reversed)
            parsed = self.parser.parse(formatted)
            transformed = self.transformer.transform(parsed)
            assert transformed == [resource, resource]
