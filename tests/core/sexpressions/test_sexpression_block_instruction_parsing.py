import pytest

import numpy

from wasm.text import parse
from wasm.datatypes import ValType
from wasm.opcodes import BinaryOpcode
from wasm.instructions.control import (
    Block,
    End,
    Nop,
    Return,
)
from wasm.instructions.numeric import (
    UnOp,
    I32Const,
)
from wasm.text.ir import NamedBlock


i32 = ValType.i32


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ("(block)", Block((), End.as_tail())),
        ("(block $blk)", NamedBlock('$blk', Block((), End.as_tail()))),
        ("(block (nop))", Block((), (Nop(),))),
        (
            "(block (result i32) (i32.ctz (return (i32.const 1))))",
            Block(
                (i32,),
                (
                    I32Const(numpy.uint32(1)),
                    UnOp.from_opcode(BinaryOpcode.I32_CTZ),
                    Return(),
                )
            ),
        ),
    ),
)
def test_sexpression_block_instructions_parsing(sexpr, expected):
    actual = parse(sexpr)
    assert actual == expected
