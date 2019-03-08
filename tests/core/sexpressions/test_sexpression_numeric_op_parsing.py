import pytest

from wasm.text import parse
from wasm.datatypes import ValType
from wasm.instructions.numeric import (
    TestOp as _TestOp,  # pytest tries to collect it otherwise
    BinOp,
    I32Const,
    I64Const,
    F32Const,
    F64Const,
    RelOp,
    Wrap,
    Extend,
)
from wasm.opcodes import BinaryOpcode


i32 = ValType.i32
i64 = ValType.i64
f32 = ValType.f32
f64 = ValType.f64


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        # simple
        ('(i32.const 1234)', I32Const(1234)),
        ('(i64.const 1234)', I64Const(1234)),
        ('(f32.const 1234)', F32Const(1234)),
        ('(f64.const 1234)', F64Const(1234)),
    ),
)
def test_sexpression_numeric_constant_parsing(sexpr, expected):
    actual = parse(sexpr)
    assert actual == expected


RELOPS = tuple(op for op in BinaryOpcode if op.is_relop)
BINOPS = tuple(op for op in BinaryOpcode if op.is_binop)
TESTOPS = tuple(op for op in BinaryOpcode if op.is_testop)
OP_PAIRS = (
    (RELOPS, RelOp),
    (BINOPS, BinOp),
    (TESTOPS, _TestOp),
)


@pytest.mark.parametrize(
    'sexpr,expected',
    tuple(
        (f'({op.text})', instruction.from_opcode(op))
        for ops, instruction in OP_PAIRS
        for op in ops
    ),
)
def test_sexpression_unop_binop_relop_instruction_parsing(sexpr, expected):
    actual = parse(sexpr)
    assert actual == expected


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ('(i32.wrap_i64)', Wrap()),
        ('(i64.extend_i32_s)', Extend.from_opcode(BinaryOpcode.I64_EXTEND_S_I32)),
        ('(i64.extend_i32_u)', Extend.from_opcode(BinaryOpcode.I64_EXTEND_U_I32)),
    ),
)
def test_sexpression_wrap_and_extend_instruction_parsing(sexpr, expected):
    actual = parse(sexpr)
    assert actual == expected
