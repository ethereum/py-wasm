import pytest

from wasm.text import parse
from wasm.datatypes import ValType
from wasm.instructions.numeric import (
    I32Const,
    I64Const,
    F32Const,
    F64Const,
)


i32 = ValType.i32
i64 = ValType.i64
f32 = ValType.f32
f64 = ValType.f64


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        # simple
        ('(i32.const 1234)', I32Const(1234)),
        ('(i64.const 1234)', I64Const(1234)),
        ('(f32.const 1234)', F32Const(1234)),
        ('(f64.const 1234)', F64Const(1234)),
    ),
)
def test_sexpression_param_parsing(sexpr, expected):
    actual = parse(sexpr)
    assert actual == expected
