#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.

import yaml
from yaml import YAMLError
from xml.etree import ElementTree as etree
from xml.etree.ElementTree import XMLParser, Element
from StringIO import StringIO

from argproc import ArgumentProcessor
from rest import http
from rest.api import request, response, collection
from rest.error import Error as HTTPReturn
from rest.filter import InputFilter, OutputFilter
from rest.resource import Resource


class ParseEntity(InputFilter):
    """Parse a request entity into a Resource."""
    
    def filter(self, input):
        ctype = request.header('Content-Type')
        if not ctype:
            raise HTTPReturn(http.BAD_REQUEST,
                    reason='Missing Content-Type header')
        try:
            type, subtype, options = http.parse_content_type(ctype)
        except ValueError:
            raise HTTPReturn(http.BAD_REQUEST,
                    reason='Illegal Content-Type header [%s]' % ctype)
        if not len(input):
            raise HTTPReturn(http.BAD_REQUEST,
                    reason='No request entity provided')
        encoding = options.get('charset')
        if type == 'text' and subtype == 'xml':
            result = self._parse_xml(input, encoding)
        elif type == 'text' and subtype in ('yaml', 'x-yaml'):
            result = self._parse_yaml(input, encoding)
        else:
            raise HTTPReturn(http.UNSUPPORTED_MEDIA_TYPE,
                             reason='Content-Type not supported [%s]' % ctype)
        return result

    def _parse_hints(self, hints):
        """Parse parser hints."""
        # XXX: this probaly needs a real parser.
        result = {}
        lines = hints.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                path, hint = line.split(':')
            except ValueError:
                raise ValueError, 'Illegal parsing hint.'
            result[path.strip()] = hint.strip()
        return result

    def _convert_xml_node(self, node, path, hints):
        """Convert an XML node into its "value" (a string, a list, or a
        Resource)."""
        if len(node) == 0:
            return node.text
        path = '%s/%s' % (path, node.tag)
        hint = hints.get(path)
        duplicate = len(set((child.tag for child in node))) != len(node)
        if hint == 'sequence' or (hint is None and duplicate):
            result = []
            for child in node:
                result.append(self._convert_xml_node(child, path, hints))
        else:
            result = Resource(node.tag)
            for child in node:
                result[child.tag] = self._convert_xml_node(child, path, hints)
        return result

    def _parse_xml(self, input, encoding):
        """Parse XML from `input' according to `encoding'."""
        if encoding and input.startswith('<?xml'):
            # The encoding from the HTTP header takes precedence. The preamble
            # is the only way in which we can pass it on to ElementTree.
            p1 = input.find('?>')
            input = input[p1+2:]
            preamble = '<?xml version="1.0" encoding="%s" ?>' % encoding
        elif not encoding and not input.startswith('<?xml'):
            # RFC2616 section 3.7.1
            preamble = '<?xml version="1.0" encoding="utf-8" ?>'
        else:
            preamble = ''
        root = etree.fromstring(preamble + input)
        hints = self._parse_hints(collection.parse_hints or '')
        resource = self._convert_xml_node(root, '', hints)
        return resource

    def _construct_yaml_resource(self, loader):
        """Construct a YAML resource node."""
        def construct(self, node):
            if isinstance(node, yaml.MappingNode):
                mapping = loader.construct_mapping(node)
                resource = Resource(node.tag[1:], mapping)
            return resource
        return construct

    def _parse_yaml(self, input, encoding):
        """Parse a YAML entity."""
        # The YAML spec mandates either UTF-8 encoding, or UTF-16 with a BOM.
        # The parser can therefore autodetect and we do not need to pass it
        # the encoding.
        # We use a Loader that turns unrecognized !tags into Resources.
        loader = yaml.Loader(input)
        loader.add_constructor(None, self._construct_yaml_resource(loader))
        try:
            parsed = loader.get_single_data()
        except YAMLError, e:
            raise HTTPReturn(http.BAD_REQUEST, reason='YAML: %s' % str(e))
        if not isinstance(parsed, dict):
            raise HTTPReturn(http.BAD_REQUEST, reason='Expecting YAML dict')
        return parsed


class FormatEntity(OutputFilter):
    """Format a Resource into a response entity."""

    def filter(self, output):
        if not isinstance(output, dict) and not isinstance(output, list):
            return output
        ctype = response.header('Content-Type')
        if ctype is None:
            accept = request.header('Accept', '*/*')
            ctype = http.select_content_type(('text/xml', 'text/yaml'), accept)
            if not ctype:
                raise HTTPReturn(http.NOT_ACCEPTABLE,
                        reason='No acceptable content-type [%s]' % accept)
        accept = request.header('Accept-Charset', '*')
        charset = http.select_charset(('utf-8',), accept)
        if not charset:
            raise HTTPReturn(http.NOT_ACCEPTABLE,
                    reason='No acceptable charset [%s]' % accept)
        response.set_header('Content-Type', '%s; charset=%s' % (ctype, charset))
        if ctype == 'text/yaml':
            output = self._format_yaml(output, charset)
        elif ctype == 'text/xml':
            output = self._format_xml(output, charset)
        return output

    def _format_xml_resource(self, value, type=None):
        """Convert a resource into an XML node."""
        if isinstance(value, dict):
            if type is None:
                type = value.get('!type')
                if not type:
                    return
            if '!type' in value:
                value = value.copy()
                del value['!type']
            node = Element(type)
            for key in value:
                child = self._format_xml_resource(value[key], key)
                if child is None:
                    continue
                node.append(child)
        elif isinstance(value, list):
            node = Element(type)
            for elem in value:
                child = self._format_xml_resource(elem, None)
                if child is None:
                    continue
                node.append(child)
        elif isinstance(value, basestring):
            node = Element(type)
            node.text = value
        elif value is None:
            node = Element(type)
        else:
            node = Element(type)
            node.text = str(value)
        return node

    def _indent_xml(self, node, level):
        """Indent a DOM tree."""
        if not len(node):
            return
        level += 2
        node.text = '\n' + level*' '
        for ix,child in enumerate(node):
            if ix == len(node)-1:
                child.tail = '\n' + (level - 2)*' '
            else:
                child.tail = '\n' + level*' '
            self._indent_xml(child, level)

    def _format_xml(self, output, encoding):
        """Convert the resource `output' into XML under the specified
        encoding."""
        root = self._format_xml_resource(output)
        self._indent_xml(root, 0)
        output = '<?xml version="1.0" encoding="%s" ?>\n' % encoding
        output += etree.tostring(root, encoding=encoding)
        return output

    def _represent_yaml_resource(self, loader):
        """Used as a YAML representer for dictionaries."""
        def format(self, data):
            if '!type' in data:
                data = data.copy()
                data.pop('!type')
            # XXX: for now do not output tags in YAML but if possible i'd like
            # to re-instate this if it appears that YAML parsers can handle
            # unknown tags reasonably well (PyYAML doesnt'...)
            #tag = '!%s' % data.pop('!type')
            tag = u'tag:yaml.org,2002:map'
            return loader.represent_mapping(tag, data)
        return format

    def _format_yaml(self, output, encoding):
        """Format a resource as YAML under the specified encoding."""
        stream = StringIO()
        dumper = yaml.Dumper(stream, default_flow_style=False, version=(1,1),
                             encoding=encoding)
        dumper.add_representer(dict, self._represent_yaml_resource(dumper))
        dumper.open()
        try:
            dumper.represent(output)
        except YAMLError, e:
            raise HTTPReturn(http.INTERNAL_SERVER_ERROR,
                             reason='YAML dump error: %s' % str(e))
        dumper.close()
        return stream.getvalue()


class FormatEntityList(FormatEntity):

    def _check_output(self, output):
        if not isinstance(output, list):
            raise HTTPReturn(http.INTERNAL_SERVER_ERROR,
                             reason='Expecting list of Resource')
        for elem in output:
            if not isinstance(elem, dict):
                raise HTTPReturn(http.INTERNAL_SERVER_ERROR,
                                 reason='Expecting list of Resource')

    def _format_xml(self, output, encoding):
        root = Element(collection.name)
        for elem in output:
            child = self._format_xml_resource(elem)
            root.append(child)
        self._indent_xml(root, 0)
        output = '<?xml version="1.0" encoding="%s" ?>\n' % encoding
        output += etree.tostring(root, encoding=encoding)
        return output


class TransformResource(InputFilter):
    """Transform a Resource from its external to its internal representation."""

    def filter(self, input):
        rules = collection.entity_transform
        if not rules:
            return input
        proc = ArgumentProcessor(namespace=collection._get_namespace())
        proc.rules(rules)
        tags = collection._get_tags()
        transformed = proc.process(input, tags=tags)
        return transformed


class ReverseResource(OutputFilter):
    """Transform a Resource from its internal to its external representation."""

    def filter(self, output):
        rules = collection.entity_transform
        if not rules:
            return output
        proc = ArgumentProcessor(namespace=collection._get_namespace())
        proc.rules(rules)
        transformed = proc.process_reverse(output)
        return transformed


class ReverseResourceList(OutputFilter):
    """Transform a list of Resource objects from their internal to their
    external representation."""

    def filter(self, output):
        rules = collection.entity_transform
        if not rules:
            return output
        proc = ArgumentProcessor(namespace=collection._get_namespace())
        proc.rules(rules)
        output = map(proc.process_reverse, output)
        return output
