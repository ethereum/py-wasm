import pytest

import numpy

from wasm.text import parse
from wasm.instructions.control import Return
from wasm.instructions.numeric import I32Const


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ("(return)", Return()),
        ("(return (i32.const 1))", (I32Const(numpy.uint32(1)), Return())),
    ),
)
def test_sexpression_return_instruction_parsing(sexpr, expected):
    actual, = parse(sexpr)
    assert actual == expected
