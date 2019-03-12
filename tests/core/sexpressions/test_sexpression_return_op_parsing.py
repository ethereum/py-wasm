import pytest

from wasm.text import parse
from wasm.instructions.control import Return


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ("(return)", Return()),
    ),
)
def test_sexpression_return_instruction_parsing(sexpr, expected):
    actual = parse(sexpr)
    assert actual == expected
