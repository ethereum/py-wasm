import pytest

from wasm.text import parse
from wasm.instructions.control import (
    Call,
)
from wasm.datatypes import (
    ValType,
    FunctionIdx,
)
from wasm.text.ir import (
    Param,
    UnresolvedFunctionType,
    UnresolvedCallIndirect,
    UnresolvedTypeIdx,
    UnresolvedFunctionIdx,
    UnresolvedCall,
)

i32 = ValType.i32
i64 = ValType.i64
f32 = ValType.f32
f64 = ValType.f64


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ("(call_indirect (result))", UnresolvedCallIndirect(UnresolvedFunctionType((), ()))),
        (
            "(call_indirect (param i64))",
            UnresolvedCallIndirect(UnresolvedFunctionType((Param(i64),), ())),
        ),
        (
            "(call_indirect (param i64) (result i32))",
            UnresolvedCallIndirect(UnresolvedFunctionType((Param(i64),), (i32,))),
        ),
        (
            "(call_indirect (type $check))",
            UnresolvedCallIndirect(UnresolvedTypeIdx('$check')),
        ),
    ),
)
def test_sexpression_call_indirect_instruction_parsing(sexpr, expected):
    actual, = parse(sexpr)
    assert actual == expected


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ("(call $func-name)", UnresolvedCall(UnresolvedFunctionIdx('$func-name'))),
        ("(call 1)", Call(FunctionIdx(1))),
    ),
)
def test_sexpression_call_instruction_parsing(sexpr, expected):
    actual, = parse(sexpr)
    assert actual == expected
