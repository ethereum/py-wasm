import pytest

from wasm.text import parse
from wasm.instructions.control import (
    Unreachable,
)


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ("(unreachable)", Unreachable()),
    ),
)
def test_sexpression_unreachable_instructions_parsing(sexpr, expected):
    actual, = parse(sexpr)
    assert actual == expected
