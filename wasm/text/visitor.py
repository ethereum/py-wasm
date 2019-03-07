import functools

import parsimonious
from parsimonious import (
    expressions,
)

from wasm._utils.decorators import (
    to_tuple,
)
from wasm._utils.toolz import (
    concatv,
)
from wasm.datatypes import (
    ValType,
)
from wasm.exceptions import (
    ParseError,
)

from .grammar import GRAMMAR
from .ir import (
    Local,
    Param,
)


def is_empty(*values):
    """
    empty is defined as:

    - falsy
    - a tuple of empty values
    """
    return all(map(_is_empty, values))


def _is_empty(value):
    if not value:
        return True
    elif isinstance(value, tuple):
        return all(_is_empty(item) for item in value)
    else:
        return False


class NodeVisitor(parsimonious.NodeVisitor):
    """
    Parsimonious node visitor which performs both parsing of type strings and
    post-processing of parse trees.  Parsing operations are cached.

    Naming conventions:

    - `lparen`: left parenthesis ')'
    - `rparen`: right parenthesis ')'
    - `ws`: whitespace
    - `txt`: the discardable text literal, aka "module" in (module ...)
    """
    grammar = GRAMMAR

    def visit_components(self, node, visited_children):
        head, tail = visited_children
        if tail:
            assert False
            return concatv(head, tuple(item for ws, item in tail))
        else:
            return head

    def visit_component_tail(self, node, visited_children):
        assert False

    def visit_component(self, node, visited_children):
        return visited_children[0]

    @staticmethod
    def _extract_simple_valtypes(node, visited_children):
        txt, ws, valtypes = visited_children
        assert is_empty(txt, ws)
        return valtypes

    #
    # Results
    #
    def visit_results(self, node, visited_children):
        head, tail = visited_children
        return tuple(concatv((head,), tail))

    def visit_results_tail(self, node, visited_children):
        ws, results = visited_children
        assert is_empty(ws)
        return results

    def visit_result(self, node, visited_children):
        lparen, txt, ws, valtypes, rparen = visited_children
        assert is_empty(lparen, txt, ws, rparen)
        return valtypes

    #
    # Locals
    #
    def visit_locals(self, node, visited_children):
        head, tail = visited_children
        return tuple(concatv(head, *tail))

    def visit_locals_tail(self, node, visited_children):
        ws, locals = visited_children
        assert is_empty(ws)
        return locals

    def visit_local(self, node, visited_children):
        lparen, locals, rparen = visited_children
        assert is_empty(lparen, rparen)
        return locals

    def visit_named_local(self, node, visited_children):
        ws0, txt, name, ws1, valtype = visited_children
        assert is_empty(ws0, txt, ws1)
        return (Local(valtype, name),)

    def visit_bare_local(self, node, visited_children):
        txt, ws, valtypes = visited_children
        assert is_empty(txt, ws)
        return tuple(Local(valtype) for valtype in valtypes)

    #
    # WASM Values
    #
    def visit_valtypes(self, node, visited_children):
        head, tail = visited_children
        return concatv((head,), tail)

    def visit_valtypes_tail(self, node, visited_children):
        ws, valtypes = visited_children
        assert is_empty(ws)
        return valtypes

    def visit_valtype(self, node, visited_children):
        return ValType.from_str(node.text)

    #
    # Simple Values
    #
    def visit_digits(self, node, visited_children):
        return int(node.text)

    def visit_name(self, node, visited_children):
        return node.text

    # Structure Values
    def visit_open(self, node, visited_children):
        return None

    def visit_close(self, node, visited_children):
        return None

    def visit_whitespace(self, node, visited_children):
        return None

    def generic_visit(self, node, visited_children):
        if isinstance(node.expr, expressions.OneOf):
            # Unwrap value chosen from alternatives
            return visited_children[0]

        if isinstance(node.expr, expressions.Optional):
            # Unwrap optional value or return `None`
            if len(visited_children) != 0:
                return visited_children[0]

            return None

        return tuple(visited_children)

    @functools.lru_cache(maxsize=None)
    def parse(self, type_str):
        """
        Parses a type string into an appropriate instance of
        :class:`~eth_abi.grammar.ABIType`.  If a type string cannot be parsed,
        throws :class:`~eth_abi.exceptions.ParseError`.

        :param type_str: The type string to be parsed.
        :returns: An instance of :class:`~eth_abi.grammar.ABIType` containing
            information about the parsed type string.
        """
        if not isinstance(type_str, str):
            raise TypeError('Can only parse string values: got {}'.format(type(type_str)))

        try:
            return super().parse(type_str)
        except parsimonious.ParseError as e:
            arst = e
            raise ParseError(e.text, e.pos, e.expr)
