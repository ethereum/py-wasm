import pytest

from wasm.text import parse
from wasm.text.ir import Local
from wasm.datatypes import ValType


i32 = ValType.i32
i64 = ValType.i64
f32 = ValType.f32
f64 = ValType.f64


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        # unnamed
        ('(local i32)', (Local(i32),)),
        ('(local i64)', (Local(i64),)),
        ('(local f32)', (Local(f32),)),
        ('(local f64)', (Local(f64),)),
        ('(local i32 i64)', (Local(i32), Local(i64))),
        ('(local f32 f64)', (Local(f32), Local(f64))),
        # named
        ('(local $i i32)', (Local(i32, '$i'),)),
        # multi
        ('(local f32 f64)\n(local $i i32)', (Local(f32), Local(f64), Local(i32, '$i'))),
    ),
)
def test_sexpression_locals_parsing(sexpr, expected):
    actual = parse(sexpr)
    assert actual == expected
