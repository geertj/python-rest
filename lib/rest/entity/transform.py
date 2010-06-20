#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import inspect

from argproc import ArgumentProcessor
from rest import http
from rest.api import application, collection, request
from rest.error import HTTPReturn
from rest.entity.hint import Hints


class Transformer(object):
    """Transform a Resource between internal and external representation."""

    def __init__(self):
        self._cache = {}

    def _get_namespace(self, collection):
        """Return the namespace for a collection."""
        namespace = {}
        module = inspect.getmodule(collection)
        namespace = module.__dict__
        if hasattr(collection, '_get_namespace'):
            namespace = collection._get_namespace(namespace)
        return namespace

    def _get_tags(self, collection, resource):
        """Return the tags for a collection."""
        tags = []
        tags.append(request.match['action'])
        if hasattr(collection, '_get_tags'):
            tags = collection._get_tags(tags, resource)
        return tags

    def _get_transform(self, resource, reverse):
        type = resource['!type']
        if type not in self._cache:
            if reverse:
                for col in application.collections.values():
                    proc = ArgumentProcessor(ignore_missing=True)
                    proc.rules(col.entity_transform)
                    result = proc.process({'!type': col.contains})
                    if result.get('!type') == type:
                        break
                else:
                    col = None
            else:
                for col in application.collections.values():
                    if col.contains == type:
                        break
                else:
                    col = None
            if col and getattr(col, 'entity_transform', None):
                proc = ArgumentProcessor()
                proc.namespace = self._get_namespace(col)
                proc.tags = self._get_tags(col, resource)
                proc.rules(col.entity_transform)
            else:
                proc = None
            self._cache[type] = proc
        proc = self._cache[type]
        return proc

    def _transform(self, resource, reverse, path=[]):
        if isinstance(resource, dict):
            if '!type' not in resource:
                if reverse:
                    raise HTTPReturn(http.INTERNAL_SERVER_ERROR,
                                     reason='Resource does not specify !type')
                elif len(path) == 0:
                    type = collection.contains
                else:
                    type = self.hints.get(path).get('type')
                    if type is None:
                        raise HTTPReturn(http.BAD_REQUEST,
                                         reason='No type hint for resource.')
                resource['!type'] = type
            path.append(None)
            for key,value in resource.items():
                path[-1] = key
                resource[key] = self._transform(value, reverse, path)
            del path[-1]
            proc = self._get_transform(resource, reverse)
            if proc:
                if reverse:
                    resource = proc.process_reverse(resource)
                else:
                    resource = proc.process(resource)
        elif isinstance(resource, list):
            for ix,elem in enumerate(resource):
                resource[ix] = self._transform(resource[ix], reverse, path)
        return resource

    def transform(self, resource, reverse=False):
        """Transform a resource between internal and external
        representation."""
        if not isinstance(resource, dict) and not isinstance(resource, list):
            return resource
        hints = Hints()
        hints.add_hints(getattr(collection, 'parse_hints', ''))
        self.hints = hints
        return self._transform(resource, reverse)
