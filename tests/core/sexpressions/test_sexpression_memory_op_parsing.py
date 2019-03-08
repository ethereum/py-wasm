import pytest

from wasm.text import parse
from wasm.instructions.memory import (
    MemoryArg,
    MemoryOp,
)
from wasm.opcodes import BinaryOpcode


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ("(i32.load)", MemoryOp.from_opcode(BinaryOpcode.I32_LOAD, MemoryArg(0, 4))),
        ("(i64.load)", MemoryOp.from_opcode(BinaryOpcode.I64_LOAD, MemoryArg(0, 8))),
        ("(f32.load)", MemoryOp.from_opcode(BinaryOpcode.F32_LOAD, MemoryArg(0, 4))),
        ("(f64.load)", MemoryOp.from_opcode(BinaryOpcode.F64_LOAD, MemoryArg(0, 8))),
        ("(i32.load8_s)", MemoryOp.from_opcode(BinaryOpcode.I32_LOAD8_S, MemoryArg(0, 1))),
        ("(i32.load8_u)", MemoryOp.from_opcode(BinaryOpcode.I32_LOAD8_U, MemoryArg(0, 1))),
        ("(i32.load16_s)", MemoryOp.from_opcode(BinaryOpcode.I32_LOAD16_S, MemoryArg(0, 2))),
        ("(i32.load16_u)", MemoryOp.from_opcode(BinaryOpcode.I32_LOAD16_U, MemoryArg(0, 2))),
        # ("(i64.load8_s)",
        # ("(i64.load8_u)",
        # ("(i64.load16_s)",
        # ("(i64.load16_u)",
        # ("(i64.load32_s)",
        # ("(i64.load32_u)",
        # ("(i32.store)",
        # ("(i64.store)",
        # ("(f32.store)",
        # ("(f64.store)",
        # ("(i32.store8)",
        # ("(i32.store16)",
        # ("(i64.store8)",
        # ("(i64.store16)",
        # ("(i64.store32)",
    ),
)
def test_sexpression_numeric_constant_parsing(sexpr, expected):
    actual = parse(sexpr)
    assert actual == expected
