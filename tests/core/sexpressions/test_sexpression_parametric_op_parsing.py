import pytest

from wasm.text import parse
from wasm.instructions.parametric import (
    Drop,
    Select,
)


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ("(drop)", Drop()),
        ("(select)", Select()),
    ),
)
def test_sexpression_parametric_instruction_parsing(sexpr, expected):
    actual, = parse(sexpr)
    assert actual == expected
