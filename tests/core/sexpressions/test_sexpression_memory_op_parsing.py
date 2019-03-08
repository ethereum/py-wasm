import pytest

from wasm.text import parse
from wasm.instructions.memory import (
    MemoryArg,
    MemoryOp,
    MemorySize,
    MemoryGrow,
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
        ("(i64.load8_s)", MemoryOp.from_opcode(BinaryOpcode.I64_LOAD8_S, MemoryArg(0, 1))),
        ("(i64.load8_u)", MemoryOp.from_opcode(BinaryOpcode.I64_LOAD8_U, MemoryArg(0, 1))),
        ("(i64.load16_s)", MemoryOp.from_opcode(BinaryOpcode.I64_LOAD16_S, MemoryArg(0, 2))),
        ("(i64.load16_u)", MemoryOp.from_opcode(BinaryOpcode.I64_LOAD16_U, MemoryArg(0, 2))),
        ("(i64.load32_s)", MemoryOp.from_opcode(BinaryOpcode.I64_LOAD32_S, MemoryArg(0, 4))),
        ("(i64.load32_u)", MemoryOp.from_opcode(BinaryOpcode.I64_LOAD32_U, MemoryArg(0, 4))),
        ("(i32.store)", MemoryOp.from_opcode(BinaryOpcode.I32_STORE, MemoryArg(0, 4))),
        ("(i64.store)", MemoryOp.from_opcode(BinaryOpcode.I64_STORE, MemoryArg(0, 8))),
        ("(f32.store)", MemoryOp.from_opcode(BinaryOpcode.F32_STORE, MemoryArg(0, 4))),
        ("(f64.store)", MemoryOp.from_opcode(BinaryOpcode.F64_STORE, MemoryArg(0, 8))),
        ("(i32.store8)", MemoryOp.from_opcode(BinaryOpcode.I32_STORE8, MemoryArg(0, 1))),
        ("(i32.store16)", MemoryOp.from_opcode(BinaryOpcode.I32_STORE16, MemoryArg(0, 2))),
        ("(i64.store8)", MemoryOp.from_opcode(BinaryOpcode.I64_STORE8, MemoryArg(0, 1))),
        ("(i64.store16)", MemoryOp.from_opcode(BinaryOpcode.I64_STORE16, MemoryArg(0, 2))),
        ("(i64.store32)", MemoryOp.from_opcode(BinaryOpcode.I64_STORE32, MemoryArg(0, 4))),
    ),
)
def test_sexpression_memory_load_and_store_parsing(sexpr, expected):
    actual = parse(sexpr)
    assert actual == expected


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ("(memory.size)", MemorySize()),
        ("(memory.grow)", MemoryGrow()),
    ),
)
def test_sexpression_memory_size_and_grow_parsing(sexpr, expected):
    actual = parse(sexpr)
    assert actual == expected
