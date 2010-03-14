#
# This file is part of Python-REST. Python-REST is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-REST is copyright (c) 2010 by the Python-REST authors. See the file
# "AUTHORS" for a complete overview.


import sys
import os.path

from ply import lex, yacc


class Parser(object):
    """Wrapper object for PLY lexer/parser."""

    exception = ValueError

    @classmethod
    def _parsetab_name(cls, fullname=True):
        """Return a name for PLY's parsetab file."""
        ptname = sys.modules[cls.__module__].__name__ + '_tab'
        if not fullname:
            ptname = ptname.split('.')[-1]
        return ptname

    @classmethod
    def _write_parsetab(cls):
        """Write parser table (distribution purposes)."""
        parser = cls()
        tabname = cls._parsetab_name(False)
        yacc.yacc(module=parser, debug=False, tabmodule=tabname)

    def parse(self, input, fname=None):
        lexer = lex.lex(object=self, debug=False)
        if hasattr(input, 'read'):
            input = input.read()
        lexer.input(input)
        self._input = input
        self._fname = fname
        parser = yacc.yacc(module=self, debug=False,
                           tabmodule=self._parsetab_name())
        parsed = parser.parse(lexer=lexer, tracking=True)
        return parsed

    def _position(self, o):
        if hasattr(o, 'lineno') and hasattr(o, 'lexpos'):
            lineno = o.lineno
            lexpos = o.lexpos
            pos = self._input.rfind('\n', 0, lexpos)
            column = lexpos - pos
        else:
            lineno = None
            column = None
        return lineno, column

    def t_ANY_error(self, t):
        err = self.exception()
        msg = 'illegal token'
        if self._fname:
            err.fname = self._fname
            msg += ' in file %s' % self._fname
            lineno, column = self._position(t)
            if lineno is not None and column is not None:
                msg += ' at %d:%d' % (lineno, column)
                err.lineno = lineno
                err.column = column
        err.args = (msg,)
        raise err

    def p_error(self, p):
        err = self.exception()
        msg = 'syntax error'
        if self._fname:
            err.fname = self._fname
            msg += ' in file %s' % self._fname
            lineno, column = self._position(p)
            if lineno is not None and column is not None:
                msg += ' at %d:%d' % (lineno, column)
                err.lineno = lineno
                err.column = column
        err.args = (msg,)
        raise err


class Field(object):

    def __init__(self, name):
        self.name = name
        self.transforms = []


class RuleParser(Parser):
    """A parser for our validation rule syntax.

    Examples:

      id <= objectid
      name <=> name *
      type <=> objecttype [default="test"]
      int(value) <=> str(value)
    """

    tokens = ('LPAREN', 'RPAREN', 'IDENTIFIER', 'ARROW', 'LEFTARROW',
              'RIGHTARROW', 'MANDATORY')

    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_IDENTIFIER = '[a-zA-Z][a-zA-Z0-9_]*'
    t_ARROW = '<=>'
    t_LEFTARROW = '<='
    t_RIGHTARROW = '=>'
    t_MANDATORY = r'\*'
    t_ignore = ' \t\n'
 
    def p_rule(self, p):
        """rule : fieldspec direction fieldspec mandatory"""
        p[0] = Rule(*p[1:])

    def p_fieldspec(self, p):
        """fieldspec : field
                     | function LPAREN fieldspec RPAREN
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[3]
            p[0].transforms.append(p[1])

    def p_field(self, p):
        """field : IDENTIFIER"""
        p[0] = Field(p[1])

    def p_function(self, p):
        """function : IDENTIFIER"""
        p[0] = p[1]

    def p_direction(self, p):
        """direction : ARROW
                     | LEFTARROW
                     | RIGHTARROW
        """
        p[0] = p[1]

    def p_mandatory(self, p):
        """mandatory : MANDATORY
                     | empty
        """
        p[0] = p[1]

    def p_empty(self, p):
        """empty : """
        p[0] = None


class Rule(object):
    """A validation rule."""

    _parser = None

    def __init__(self, left, direction, right, mandatory):
        self.left = left
        self.direction = direction
        self.right = right
        self.mandatory = mandatory

    @classmethod
    def parse(cls, rule):
        if cls._parser is None:
            cls._parser = RuleParser()
        rule = cls._parser.parse(rule)
        return rule


class ValidationError(Exception):
    """Validation error."""


class Validator(object):
    """Rule based validation."""

    def __init__(self, ignore_unknown=False):
        self.rules = []
        self.ignore_unknown = ignore_unknown

    def rule(self, rule):
        rule = Rule.parse(rule)
        rule.globals = globals()
        self.rules.append(rule)

    def validate(self, input):
        validated = {}  
        for rule in self.rules:
            if rule.direction not in ('=>', '<=>'):
                continue
            name = rule.left.name
            if name in input:
                value = input[name]
                newname = rule.right.name
                for xform in rule.left.transforms:
                    xform = eval(xform, rule.globals)
                    value = xform(value)
                validated[newname] = value
            elif rule.mandatory:
                raise ValidationError, 'Missing required input: %s' % name
        for key in input:
            for rule in self.rules:
                if key == rule.left.name:
                    break
            else:
                raise ValidationError, 'Unknown input encountered: %s' % key
        return validated

    def reverse(self, output):
        reversed = {}
        for rule in self.rules:
            if rule.direction not in ('<=', '<=>'):
                continue
            name = rule.right.name
            if name in output:
                value = output[name]
                newname = rule.left.name
                for xform in rule.right.transforms:
                    xform = eval(xform, rule.globals)
                    value = xform(value)
                reversed[newname] = value
        for key in output:
            for rule in self.rules:
                if key == rule.right.name:
                    break
            else:
                raise ValidationError, 'Don\'t know how to reverse: %s' % key
        return reversed
