import pytest

from wasm.text import parse
from wasm.datatypes import ValType
from wasm.instructions.numeric import (
    Reinterpret,
    Demote,
    Promote,
    Convert,
    TestOp as _TestOp,  # pytest tries to collect it otherwise
    BinOp,
    I32Const,
    I64Const,
    F32Const,
    F64Const,
    RelOp,
    Wrap,
    UnOp,
    Extend,
    Truncate,
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
    actual, = parse(sexpr)
    assert actual == expected


UNOPS = tuple(op for op in BinaryOpcode if op.is_unop)
RELOPS = tuple(op for op in BinaryOpcode if op.is_relop)
BINOPS = tuple(op for op in BinaryOpcode if op.is_binop)
TESTOPS = tuple(op for op in BinaryOpcode if op.is_testop)
OP_PAIRS = (
    (UNOPS, UnOp),
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
    actual, = parse(sexpr)
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
    actual, = parse(sexpr)
    assert actual == expected


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ('(i32.trunc_f32_s)', Truncate.from_opcode(BinaryOpcode.I32_TRUNC_S_F32)),
        ('(i32.trunc_f32_u)', Truncate.from_opcode(BinaryOpcode.I32_TRUNC_U_F64)),
        ('(i32.trunc_f64_s)', Truncate.from_opcode(BinaryOpcode.I32_TRUNC_S_F32)),
        ('(i32.trunc_f64_u)', Truncate.from_opcode(BinaryOpcode.I32_TRUNC_U_F64)),
        ('(i64.trunc_f32_s)', Truncate.from_opcode(BinaryOpcode.I64_TRUNC_S_F32)),
        ('(i64.trunc_f32_u)', Truncate.from_opcode(BinaryOpcode.I64_TRUNC_U_F64)),
        ('(i64.trunc_f64_s)', Truncate.from_opcode(BinaryOpcode.I64_TRUNC_S_F32)),
        ('(i64.trunc_f64_u)', Truncate.from_opcode(BinaryOpcode.I64_TRUNC_U_F64)),
    )
)
def test_sexpression_trunc_instruction_parsing(sexpr, expected):
    actual, = parse(sexpr)
    assert actual == expected


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ('(f32.convert_i32_s)', Convert.from_opcode(BinaryOpcode.F32_CONVERT_S_I32)),
        ('(f32.convert_i32_u)', Convert.from_opcode(BinaryOpcode.F32_CONVERT_U_I32)),
        ('(f32.convert_i64_s)', Convert.from_opcode(BinaryOpcode.F32_CONVERT_S_I64)),
        ('(f32.convert_i64_u)', Convert.from_opcode(BinaryOpcode.F32_CONVERT_U_I64)),
        ('(f64.convert_i32_s)', Convert.from_opcode(BinaryOpcode.F64_CONVERT_S_I32)),
        ('(f64.convert_i32_u)', Convert.from_opcode(BinaryOpcode.F64_CONVERT_U_I32)),
        ('(f64.convert_i64_s)', Convert.from_opcode(BinaryOpcode.F64_CONVERT_S_I64)),
        ('(f64.convert_i64_u)', Convert.from_opcode(BinaryOpcode.F64_CONVERT_U_I64)),
    )
)
def test_sexpression_convert_instruction_parsing(sexpr, expected):
    actual, = parse(sexpr)
    assert actual == expected


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ('(f32.demote_f64)', Demote()),
        ('(f64.promote_f32)', Promote()),
    ),
)
def test_sexpression_demote_and_promote_instruction_parsing(sexpr, expected):
    actual, = parse(sexpr)
    assert actual == expected


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ('(i32.reinterpret_f32)', Reinterpret.from_opcode(BinaryOpcode.I32_REINTERPRET_F32)),
        ('(i64.reinterpret_f64)', Reinterpret.from_opcode(BinaryOpcode.I64_REINTERPRET_F64)),
        ('(f32.reinterpret_i32)', Reinterpret.from_opcode(BinaryOpcode.F32_REINTERPRET_I32)),
        ('(f64.reinterpret_i64)', Reinterpret.from_opcode(BinaryOpcode.F64_REINTERPRET_I64)),
    )
)
def test_sexpression_reinterpret_instruction_parsing(sexpr, expected):
    actual, = parse(sexpr)
    assert actual == expected
