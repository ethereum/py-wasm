import pytest

from wasm.text import parse
from wasm.datatypes import MemoryType


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        #('(memory 1)', MemoryType(1)),
    ),
)
def test_sexpression_memory_type_parsing(sexpr, expected):
    actual = parse(sexpr)
    assert actual == expected
