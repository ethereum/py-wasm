import pytest

from wasm.text import parse
from wasm.datatypes import ValType


i32 = ValType.i32
i64 = ValType.i64
f32 = ValType.f32
f64 = ValType.f64


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        # simple
        ('(result i32)', ((i32,),)),
        ('(result i32 i64)', ((i32, i64),)),
        # many
        ('(result i32) (result i64)', ((i32,), (i64,))),
    ),
)
def test_sexpression_results_parsing(sexpr, expected):
    actual = parse(sexpr)
    assert actual == expected
