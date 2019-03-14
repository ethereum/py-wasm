import pytest

from wasm.text import parse
from wasm.instructions.control import (
    Nop
)


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ("(nop)", Nop()),
    ),
)
def test_sexpression_nop_instructions_parsing(sexpr, expected):
    actual, = parse(sexpr)
    assert actual == expected
