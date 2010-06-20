#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import sys
import time
import logging
import httplib as http

from threading import Thread
from httplib import HTTPConnection
from xml.etree import ElementTree as etree
from xml.etree.ElementTree import XML, Element

from rest import Application, Collection, Resource
from rest.api import request, response, mapper
from rest.server import make_server


class BookCollection(Collection):

    name = 'books'
    contains = 'book'

    entity_transform = """
        $!type <=> $!type
        $id:int <=> $id
        $title <=> $title
        $reviews <= $reviews
        """


    def __init__(self):
        self.books = []
        self.books.append(Resource('book', { 'id': '1', 'title': 'Book Number 1' } ))
        self.books.append(Resource('book', { 'id': '2', 'title': 'Book Number 1' } ))
        self.books.append(Resource('book', { 'id': '3', 'title': 'Book Number 1' } ))

    def _get_book(self, id):
        for book in self.books:
            if book['id'] == id:
                return book

    def show(self, id):
        book = self._get_book(id)
        if not book:
            raise KeyError
        return book

    def list(self, **kwargs):
        match = []
        id = kwargs.get('id')
        detail = kwargs.get('detail')
        for book in self.books:
            if id and book['id'] != id:
                continue
            book = book.copy()
            if detail == '2':
                book['reviews'] = [Resource('review',
                                          { 'comment': 'Very good' })]
            match.append(book)
        return match

    def create(self, input):
        self.books.append(input)
        url = mapper.url_for(collection=self.name, action='show',
                             id=input['id'])
        return url

    def update(self, id, input):
        book = self._get_book(id)
        if not book:
            raise KeyError
        book.update(input)

    def delete(self, id):
        book = self._get_book(id)
        if not book:
            raise KeyError
        self.books.remove(book)


class BookApplication(Application):

    def setup_collections(self):
        self.add_collection(BookCollection())


class TestApplication(object):

    @classmethod
    def setUpClass(cls):
        # Make sure we get some logs on standard output.
        level = logging.DEBUG
        logger = logging.getLogger('rest')
        handler = logging.StreamHandler(sys.stdout)
        format = '%(levelname)s [%(name)s] %(message)s'
        formatter = logging.Formatter(format)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
        
    def setUp(self):
        self.server = make_server('localhost', 0, BookApplication)
        # don't want any logging
        self.server.RequestHandlerClass.log_request = lambda *args: None
        self.thread = Thread(target=self.server.serve_forever)
        self.thread.start()
        time.sleep(0.5)  # make sure server is started up
        address = self.server.socket.getsockname()
        self.client = HTTPConnection(*address)

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()

    def test_show(self):
        client = self.client
        client.request('GET', '/api/books/1')
        response = client.getresponse()
        assert response.status == http.OK
        assert response.getheader('Content-Type') == 'text/xml; charset=utf-8'
        xml = etree.fromstring(response.read())
        assert etree.tostring(xml) == \
                '<book>\n  <id>1</id>\n  <title>Book Number 1</title>\n</book>'

    def test_show_not_found(self):
        client = self.client
        client.request('GET', '/api/books/4')
        response = client.getresponse()
        assert response.status == http.NOT_FOUND

    def test_show_with_input(self):
        client = self.client
        client.request('GET', '/api/books/1', 'body input')
        response = client.getresponse()
        assert response.status == http.BAD_REQUEST

    def test_list(self):
        client = self.client
        client.request('GET', '/api/books')
        response = client.getresponse()
        assert response.status == http.OK
        assert response.getheader('Content-Type') == 'text/xml; charset=utf-8'
        xml = etree.fromstring(response.read())
        assert len(xml.findall('.//id')) == 3

    def test_list_with_input(self):
        client = self.client
        client.request('GET', '/api/books', 'body input')
        response = client.getresponse()
        assert response.status == http.BAD_REQUEST

    def test_list_with_filter(self):
        client = self.client
        client.request('GET', '/api/books?id=2')
        response = client.getresponse()
        assert response.status == http.OK
        assert response.getheader('Content-Type') == 'text/xml; charset=utf-8'
        xml = etree.fromstring(response.read())
        assert len(xml.findall('.//id')) == 1

    def test_create(self):
        client = self.client
        book = XML('<book><id>4</id><title>Book Number 4</title></book>')
        headers = { 'Content-Type': 'text/xml' }
        client.request('POST', '/api/books', etree.tostring(book), headers)
        response = client.getresponse()
        assert response.status == http.CREATED
        assert response.getheader('Location').endswith('/api/books/4')

    def test_create_no_input(self):
        client = self.client
        client.request('POST', '/api/books')
        response = client.getresponse()
        assert response.status == http.BAD_REQUEST

    def test_create_wrong_content_type(self):
        client = self.client
        book = '<book><id>4</id><title>Book Number 4</title></book>'
        headers = { 'Content-Type': 'text/plain' }
        client.request('POST', '/api/books', book, headers)
        response = client.getresponse()
        assert response.status == http.UNSUPPORTED_MEDIA_TYPE

    def test_delete(self):
        client = self.client
        client.request('DELETE', '/api/books/1')
        response = client.getresponse()
        assert response.status == http.NO_CONTENT

    def test_delete_non_existent(self):
        client = self.client
        client.request('DELETE', '/api/books/4')
        response = client.getresponse()
        assert response.status == http.NOT_FOUND

    def test_delete_with_input(self):
        client = self.client
        client.request('DELETE', '/api/books/4', 'input')
        response = client.getresponse()
        assert response.status == http.BAD_REQUEST

    def test_update(self):
        client = self.client
        book = XML('<book><id>1</id><title>Book Number 2</title></book>')
        headers = { 'Content-Type': 'text/xml' }
        client.request('PUT', '/api/books/1', etree.tostring(book), headers)
        response = client.getresponse()
        assert response.status == http.NO_CONTENT

    def test_update_without_input(self):
        client = self.client
        headers = { 'Content-Type': 'text/xml' }
        client.request('PUT', '/api/books/1', '', headers)
        response = client.getresponse()
        assert response.status == http.BAD_REQUEST

    def test_update_with_wrong_content_type(self):
        client = self.client
        book = '<book><id>1</id><title>Book Number 2</title></book>'
        headers = { 'Content-Type': 'text/plain' }
        client.request('PUT', '/api/books/1', book, headers)
        response = client.getresponse()
        assert response.status == http.UNSUPPORTED_MEDIA_TYPE

    def test_update_non_existent(self):
        client = self.client
        book = XML('<book><id>1</id><title>Book Number 2</title></book>')
        headers = { 'Content-Type': 'text/xml' }
        client.request('PUT', '/api/books/4', etree.tostring(book), headers)
        response = client.getresponse()
        assert response.status == http.NOT_FOUND

    def test_wrong_methods(self):
        client = self.client
        client.request('PUT', '/api/books')
        response = client.getresponse()
        assert response.status == http.METHOD_NOT_ALLOWED
        allowed = set(response.getheader('Allowed').split(', '))
        assert allowed == set(['GET', 'POST'])
        client.request('DELETE', '/api/books')
        response = client.getresponse()
        assert response.status == http.METHOD_NOT_ALLOWED
        allowed = set(response.getheader('Allowed').split(', '))
        assert allowed == set(['GET', 'POST'])
        client.request('POST', '/api/books/1')
        response = client.getresponse()
        assert response.status == http.METHOD_NOT_ALLOWED
        allowed = set(response.getheader('Allowed').split(', '))
        assert allowed == set(['GET', 'DELETE', 'PUT'])
