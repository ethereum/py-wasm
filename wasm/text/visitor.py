import functools

import parsimonious
from parsimonious import (
    expressions,
)

from wasm._utils.decorators import (
    to_tuple,
)
from wasm._utils.toolz import (
    cons,
    concatv,
)
from wasm.datatypes import (
    TypeIdx,
    LabelIdx,
    ValType,
    FunctionIdx,
)
from wasm.exceptions import (
    ParseError,
)
from wasm.instructions.control import (
    Call,
    Return,
    Br,
    BrIf,
    BrTable,
)
from wasm.instructions.variable import (
    LocalOp,
    GlobalOp,
)
from wasm.instructions.parametric import (
    Drop,
    Select,
)
from wasm.instructions.numeric import (
    Reinterpret,
    Demote,
    Promote,
    Convert,
    I32Const,
    BinOp,
    I64Const,
    F32Const,
    F64Const,
    RelOp,
    TestOp,
    Wrap,
    Extend,
    Truncate,
)
from wasm.instructions.memory import (
    MemoryArg,
    MemoryOp,
    MemorySize,
    MemoryGrow,
)
from wasm.opcodes import (
    BinaryOpcode,
    TEXT_TO_OPCODE,
)

from .grammar import GRAMMAR
from .ir import (
    Local,
    Param,
    UnresolvedCall,
    UnresolvedVariableOp,
    UnresolvedCallIndirect,
    UnresolvedTypeIdx,
    UnresolvedFunctionIdx,
    UnresolvedFunctionType,
    UnresolvedBr,
    UnresolvedBrIf,
    UnresolvedBrTable,
    UnresolvedLabelIdx,
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


TRUNC_LOOKUP = {
    'i32.trunc_f32_s': BinaryOpcode.I32_TRUNC_S_F32,
    'i32.trunc_f32_u': BinaryOpcode.I32_TRUNC_U_F64,
    'i32.trunc_f64_s': BinaryOpcode.I32_TRUNC_S_F32,
    'i32.trunc_f64_u': BinaryOpcode.I32_TRUNC_U_F64,
    'i64.trunc_f32_s': BinaryOpcode.I64_TRUNC_S_F32,
    'i64.trunc_f32_u': BinaryOpcode.I64_TRUNC_U_F64,
    'i64.trunc_f64_s': BinaryOpcode.I64_TRUNC_S_F32,
    'i64.trunc_f64_u': BinaryOpcode.I64_TRUNC_U_F64,
}
CONVERT_LOOKUP = {
    'f32.convert_i32_s': BinaryOpcode.F32_CONVERT_S_I32,
    'f32.convert_i32_u': BinaryOpcode.F32_CONVERT_U_I32,
    'f32.convert_i64_s': BinaryOpcode.F32_CONVERT_S_I64,
    'f32.convert_i64_u': BinaryOpcode.F32_CONVERT_U_I64,
    'f64.convert_i32_s': BinaryOpcode.F64_CONVERT_S_I32,
    'f64.convert_i32_u': BinaryOpcode.F64_CONVERT_U_I32,
    'f64.convert_i64_s': BinaryOpcode.F64_CONVERT_S_I64,
    'f64.convert_i64_u': BinaryOpcode.F64_CONVERT_U_I64,
}
REINTERPRET_LOOKUP = {
    'i32.reinterpret_f32': BinaryOpcode.I32_REINTERPRET_F32,
    'i64.reinterpret_f64': BinaryOpcode.I64_REINTERPRET_F64,
    'f32.reinterpret_i32': BinaryOpcode.F32_REINTERPRET_I32,
    'f64.reinterpret_i64': BinaryOpcode.F64_REINTERPRET_I64,
}
MEMORY_ARG_DEFAULTS = {
    BinaryOpcode.I32_LOAD: MemoryArg(0, 4),
    BinaryOpcode.I64_LOAD: MemoryArg(0, 8),
    BinaryOpcode.F32_LOAD: MemoryArg(0, 4),
    BinaryOpcode.F64_LOAD: MemoryArg(0, 8),
    BinaryOpcode.I32_LOAD8_S: MemoryArg(0, 1),
    BinaryOpcode.I32_LOAD8_U: MemoryArg(0, 1),
    BinaryOpcode.I32_LOAD16_S: MemoryArg(0, 2),
    BinaryOpcode.I32_LOAD16_U: MemoryArg(0, 2),
    BinaryOpcode.I64_LOAD8_S: MemoryArg(0, 1),
    BinaryOpcode.I64_LOAD8_U: MemoryArg(0, 1),
    BinaryOpcode.I64_LOAD16_S: MemoryArg(0, 2),
    BinaryOpcode.I64_LOAD16_U: MemoryArg(0, 2),
    BinaryOpcode.I64_LOAD32_S: MemoryArg(0, 4),
    BinaryOpcode.I64_LOAD32_U: MemoryArg(0, 4),
    BinaryOpcode.I32_STORE: MemoryArg(0, 4),
    BinaryOpcode.I64_STORE: MemoryArg(0, 8),
    BinaryOpcode.F32_STORE: MemoryArg(0, 4),
    BinaryOpcode.F64_STORE: MemoryArg(0, 8),
    BinaryOpcode.I32_STORE8: MemoryArg(0, 1),
    BinaryOpcode.I32_STORE16: MemoryArg(0, 2),
    BinaryOpcode.I64_STORE8: MemoryArg(0, 1),
    BinaryOpcode.I64_STORE16: MemoryArg(0, 2),
    BinaryOpcode.I64_STORE32: MemoryArg(0, 4),
}


@to_tuple
def process_vars(resolved_cls, unresolved_cls, vars):
    for var in vars:
        if isinstance(var, str):
            yield unresolved_cls(var)
        elif isinstance(var, int):
            yield resolved_cls(var)
        else:
            raise Exception("INVALID")


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
        return tuple(cons(head, tail))

    #
    # Control ops
    #
    def visit_control_op(self, node, visited_children):
        lparen, instruction, rparen = visited_children
        assert is_empty(lparen, rparen)
        return instruction

    def visit_br_table_op(self, node, visited_children):
        txt, ws, all_label_indices = visited_children
        assert is_empty(txt, ws)
        is_resolved = (
            all(isinstance(label_idx, int) for label_idx in all_label_indices)
        )
        *label_indices, default_idx = process_vars(LabelIdx, UnresolvedLabelIdx, all_label_indices)
        if is_resolved:
            return BrTable(
                label_indices=tuple(label_indices),
                default_idx=default_idx,
            )
        else:
            return UnresolvedBrTable(
                label_indices=tuple(label_indices),
                default_idx=default_idx,
            )

    def visit_br_if_op(self, node, visited_children):
        txt, ws, label_idx = visited_children
        assert is_empty(txt, ws)
        if isinstance(label_idx, int):
            return BrIf(LabelIdx(label_idx))
        elif isinstance(label_idx, str):
            return UnresolvedBrIf(UnresolvedLabelIdx(label_idx))
        else:
            raise Exception("INVALID")

    def visit_br_op(self, node, visited_children):
        txt, ws, label_idx = visited_children
        assert is_empty(txt, ws)
        if isinstance(label_idx, int):
            return Br(LabelIdx(label_idx))
        elif isinstance(label_idx, str):
            return UnresolvedBr(UnresolvedLabelIdx(label_idx))
        else:
            raise Exception("INVALID")

    def visit_return_op(self, node, visited_children):
        return Return()

    def visit_call_op(self, node, visited_children):
        txt, ws, function_idx = visited_children

        if isinstance(function_idx, str):
            return UnresolvedCall(UnresolvedFunctionIdx(function_idx))
        elif isinstance(function_idx, int):
            return Call(FunctionIdx(function_idx))
        else:
            raise Exception("INVALID")

    def visit_call_indirect_op(self, node, visited_children):
        txt, ws, typeuse = visited_children
        assert is_empty(txt, ws)

        if len(typeuse) == 2:
            params, results = typeuse
            func_type = UnresolvedFunctionType(params, results)
            return UnresolvedCallIndirect(func_type)
        elif isinstance(typeuse, UnresolvedTypeIdx):
            return UnresolvedCallIndirect(typeuse)
        else:
            raise Exception("INVALID")

    #
    # Function Type
    #
    def visit_func_type(self, node, visited_children):
        lparen, txt, ws, func_type, rparen = visited_children
        assert is_empty(lparen, txt, ws, rparen)
        return func_type

    def visit_typeuse(self, node, visited_children):
        typeuse, = visited_children
        if isinstance(typeuse, TypeIdx):
            return typeuse
        elif isinstance(typeuse, UnresolvedFunctionType):
            return typeuse
        elif isinstance(typeuse, UnresolvedTypeIdx):
            return typeuse
        elif is_empty(*visited_children):
            return UnresolvedFunctionType((), ())
        elif isinstance(typeuse, tuple) and all(isinstance(item, Param) for item in typeuse):
            return UnresolvedFunctionType(typeuse, ())
        elif isinstance(typeuse, tuple) and all(isinstance(item, ValType) for item in typeuse):
            return UnresolvedFunctionType((), typeuse)
        else:
            raise Exception("INVALID")

    def visit_typeuse_direct(self, node, visited_children):
        lparen, text, ws, var, rparen = visited_children
        assert is_empty(lparen, text, ws, rparen)
        if isinstance(var, str):
            return UnresolvedTypeIdx(var)
        elif isinstance(var, int):
            return TypeIdx(var)
        else:
            raise Exception("INVALID")

    def visit_typeuse_params_and_results(self, node, visited_children):
        params, ws, results = visited_children
        assert is_empty(ws)

        if params is None:
            params = tuple()

        if results is None:
            results = tuple()

        return UnresolvedFunctionType(params, results)

    #
    # Parametric ops
    #
    def visit_parametric_op(self, node, visited_children):
        lparen, instruction, rparen = visited_children
        assert is_empty(lparen, rparen)
        return instruction

    def visit_any_parametric_op(self, node, visited_children):
        if node.text == "drop":
            return Drop()
        elif node.text == "select":
            return Select()
        else:
            raise Exception("INVALID")

    #
    # Variable ops
    #
    def visit_variable_op(self, node, visited_children):
        lparen, instruction, rparen = visited_children
        assert is_empty(lparen, rparen)
        return instruction

    def visit_any_variable_op(self, node, visited_children):
        (instruction_class, opcode), ws, var = visited_children
        if isinstance(var, str):
            return UnresolvedVariableOp(opcode, var)
        else:
            return instruction_class.from_opcode(opcode, var)

    def visit_local_variable_op(self, node, visited_children):
        _, _, action = node.text.partition('.')
        if action == 'get':
            return LocalOp, BinaryOpcode.GET_LOCAL
        elif action == 'set':
            return LocalOp, BinaryOpcode.SET_LOCAL
        elif action == 'tee':
            return LocalOp, BinaryOpcode.TEE_LOCAL
        else:
            raise Exception("INVALID")

    def visit_global_variable_op(self, node, visited_children):
        _, _, action = node.text.partition('.')
        if action == 'get':
            return GlobalOp, BinaryOpcode.GET_GLOBAL
        elif action == 'set':
            return GlobalOp, BinaryOpcode.SET_GLOBAL
        else:
            raise Exception("INVALID")

    #
    # Memory ops
    #
    def visit_memory_op(self, node, visited_children):
        lparen, instruction, rparen = visited_children
        assert is_empty(lparen, rparen)
        return instruction

    def visit_memory_size_op(self, node, visited_children):
        return MemorySize()

    def visit_memory_grow_op(self, node, visited_children):
        return MemoryGrow()

    def visit_memory_access_op(self, node, visited_children):
        memarg, = visited_children

        opcode = TEXT_TO_OPCODE[node.text]
        if memarg is None:
            memarg = MEMORY_ARG_DEFAULTS[opcode]
        else:
            assert isinstance(memarg, MemoryArg)

        return MemoryOp.from_opcode(opcode, memarg)

    def visit_memory_store_float_op(self, node, visited_children):
        valtype, txt, tail = visited_children
        assert is_empty(valtype, txt)
        if tail is None:
            return None
        raise Exception("UNHANDLED")

    def visit_memory_store_integer_op(self, node, visited_children):
        valtype, txt, tail = visited_children
        assert is_empty(valtype, txt)
        if tail is None:
            return None
        else:
            size, memarg = tail
            assert is_empty(size)
            return memarg

    def visit_memory_load_float_op(self, node, visited_children):
        # TODO: identical to `visit_memory_store_float_op`
        valtype, txt, tail = visited_children
        assert is_empty(valtype, txt)
        if tail is None:
            return None
        raise Exception("UNHANDLED")

    def visit_memory_load_integer_op(self, node, visited_children):
        valtype, txt, tail = visited_children
        assert is_empty(valtype, txt)
        if tail is None:
            return None
        else:
            size, ws, _, memarg = tail
            assert is_empty(size, ws)
            return memarg

    def visit_memory_arg(self, node, visited_children):
        offset, align = visited_children
        if offset is None and align is None:
            return None
        elif offset is None or align is None:
            raise Exception("INVALID")
        else:
            return MemoryArg(offset, align)

    def visit_offset(self, node, visited_children):
        assert False

    def visit_align(self, node, visited_children):
        assert False

    #
    # Numeric ops
    #
    def visit_numeric_op(self, node, visited_children):
        lparen, instruction, rparen = visited_children
        assert is_empty(lparen, rparen)
        return instruction

    def visit_constop(self, node, visited_children):
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

    def visit_truncop(self, node, visited_children):
        opcode = TRUNC_LOOKUP[node.text]
        return Truncate.from_opcode(opcode)

    def visit_convertop(self, node, visited_children):
        opcode = CONVERT_LOOKUP[node.text]
        return Convert.from_opcode(opcode)

    def visit_demoteop(self, node, visited_children):
        return Demote()

    def visit_promoteop(self, node, visited_children):
        return Promote()

    def visit_reinterpretop(self, node, visited_children):
        opcode = REINTERPRET_LOOKUP[node.text]
        return Reinterpret.from_opcode(opcode)

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
        return self._join_multi_head_with_tail(node, visited_children)

    def visit_results_tail(self, node, visited_children):
        return self._process_tail(node, visited_children)

    def visit_result(self, node, visited_children):
        lparen, valtypes, rparen = visited_children
        assert is_empty(lparen, rparen)
        return valtypes

    def visit_declared_result(self, node, visited_children):
        txt, ws, valtypes = visited_children
        assert is_empty(txt, ws)
        return valtypes

    def visit_empty_result(self, node, visited_children):
        return tuple()

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

    def visit_vars_tail(self, node, visited_children):
        ws, var = visited_children
        assert is_empty(ws)
        return var

    def visit_vars(self, node, visited_children):
        head, tail = visited_children
        return tuple(cons(head, tail))

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
        if not isinstance(type_str, str):
            raise TypeError('Can only parse string values: got {}'.format(type(type_str)))

        try:
            return super().parse(type_str)
        except parsimonious.ParseError as e:
            arst = e  # noqa: F841
            raise ParseError(e.text, e.pos, e.expr)
