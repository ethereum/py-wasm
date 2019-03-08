import functools

import parsimonious
from parsimonious import (
    expressions,
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
from wasm.instructions.numeric import (
    I32Const,
    BinOp,
    I64Const,
    F32Const,
    F64Const,
    RelOp,
    TestOp,
    Wrap,
    Extend,
)
from wasm.opcodes import (
    BinaryOpcode,
    TEXT_TO_OPCODE,
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

    def visit_component(self, node, visited_children):
        return visited_children[0]

    @staticmethod
    def _process_tail(node, visited_children):
        ws, tail = visited_children
        assert is_empty(ws)
        return tail

    @staticmethod
    def _join_multi_head_with_tail(node, visited_children):
        head, tail = visited_children
        return tuple(concatv(head, *tail))

    @staticmethod
    def _join_single_head_with_tail(node, visited_children):
        head, tail = visited_children
        return tuple(concatv((head,), tail))

    #
    # Numeric ops
    #
    def visit_numeric_op(self, node, visited_children):
        lparen, instruction, rparen = visited_children
        assert is_empty(lparen, rparen)
        return instruction

    #
    # Numeric RelOp
    #
    def visit_extendop(self, node, visited_children):
        i64, txt, i32, _, sign = visited_children
        assert is_empty(i64, txt, i32, _)

        if sign is True:
            return Extend.from_opcode(BinaryOpcode.I64_EXTEND_S_I32)
        elif sign is False:
            return Extend.from_opcode(BinaryOpcode.I64_EXTEND_U_I32)
        else:
            raise Exception("INVALID")

    def visit_wrapop(self, node, visited_children):
        return Wrap()

    def visit_testop(self, node, visited_children):
        opcode = TEXT_TO_OPCODE[node.text]
        return TestOp.from_opcode(opcode)

    def visit_relop(self, node, visited_children):
        opcode = TEXT_TO_OPCODE[node.text]
        return RelOp.from_opcode(opcode)

    def visit_binop(self, node, visited_children):
        opcode = TEXT_TO_OPCODE[node.text]
        return BinOp.from_opcode(opcode)

    #
    # Numeric Constant
    #
    def visit_inner_numeric_const(self, node, visited_children):
        valtype, txt, ws, value = visited_children
        assert is_empty(txt, ws)
        if valtype is ValType.i32:
            return I32Const(value)
        elif valtype is ValType.i64:
            return I64Const(value)
        elif valtype is ValType.f32:
            return F32Const(value)
        elif valtype is ValType.f64:
            return F64Const(value)
        else:
            raise Exception("INVALID")

    #
    # Params
    #
    def visit_params(self, node, visited_children):
        return self._join_multi_head_with_tail(node, visited_children)

    def visit_params_tail(self, node, visited_children):
        return self._process_tail(node, visited_children)

    def visit_param(self, node, visited_children):
        lparen, params, rparen = visited_children
        assert is_empty(lparen, rparen)
        return params

    def visit_named_param(self, node, visited_children):
        ws0, txt, name, ws1, valtype = visited_children
        assert is_empty(ws0, txt, ws1)
        return (Param(valtype, name),)

    def visit_bare_param(self, node, visited_children):
        txt, ws, valtypes = visited_children
        assert is_empty(txt, ws)
        return tuple(Param(valtype) for valtype in valtypes)

    #
    # Results
    #
    def visit_results(self, node, visited_children):
        return self._join_single_head_with_tail(node, visited_children)

    def visit_results_tail(self, node, visited_children):
        return self._process_tail(node, visited_children)

    def visit_result(self, node, visited_children):
        lparen, txt, ws, valtypes, rparen = visited_children
        assert is_empty(lparen, txt, ws, rparen)
        return valtypes

    #
    # Locals
    #
    def visit_locals(self, node, visited_children):
        return self._join_multi_head_with_tail(node, visited_children)

    def visit_locals_tail(self, node, visited_children):
        return self._process_tail(node, visited_children)

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
        return tuple(concatv((head,), tail))

    def visit_valtypes_tail(self, node, visited_children):
        return self._process_tail(node, visited_children)

    def visit_valtype(self, node, visited_children):
        return ValType.from_str(node.text)

    #
    # Simple Values
    #
    def visit_sign(self, node, visited_children):
        if node.text == 's':
            return True
        elif node.text == 'u':
            return False
        else:
            raise Exception("INVALID")

    def visit_num(self, node, visited_children):
        return int(node.text)

    def visit_name(self, node, visited_children):
        return node.text

    #
    # Structure Values
    #
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
