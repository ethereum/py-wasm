import pytest

from wasm.text import parse
from wasm.datatypes import (
    ValType,
)
from wasm.text.ir import (
    Param,
    UnresolvedFunctionType,
)

i32 = ValType.i32
i64 = ValType.i64
f32 = ValType.f32
f64 = ValType.f64


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ("(func (param))", UnresolvedFunctionType((), ())),
        ("(func (param) (param))", UnresolvedFunctionType((), ())),
        ("(func (param i32))", UnresolvedFunctionType((Param(i32),), ())),
        ("(func (param $x i32))", UnresolvedFunctionType((Param(i32, '$x'),), ())),
        (
            "(func (param i32 f64 i64))",
            UnresolvedFunctionType((Param(i32), Param(f64), Param(i64)), ()),
        ),
        ("(func (param i32) (param f64))", UnresolvedFunctionType((Param(i32), Param(f64)), ())),
        (
            "(func (param i32 f32) (param $x i64) (param) (param i32 f64))",
            UnresolvedFunctionType(
                (Param(i32), Param(f32), Param(i64, '$x'), Param(i32), Param(f64)),
                (),
            ),
        ),

        # ("(func (result i32) (unreachable))  # TODO: this is not a raw functype but rather a `function` definition.
    ),
)
def test_sexpression_parametric_instruction_parsing(sexpr, expected):
    actual = parse(sexpr)
    assert actual == expected
