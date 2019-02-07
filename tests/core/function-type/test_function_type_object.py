import pytest

from wasm.datatypes import (
    FunctionType,
    ValType,
)


@pytest.mark.parametrize(
    'function_type_a,function_type_b,expected',
    (
        (
            FunctionType(tuple(), tuple()),
            FunctionType(tuple(), tuple()),
            True,
        ),
        (
            FunctionType((ValType.i32,), tuple()),
            FunctionType((ValType.i32,), tuple()),
            True,
        ),
        (
            FunctionType(tuple(), (ValType.i32,)),
            FunctionType(tuple(), (ValType.i32,)),
            True,
        ),
        (
            FunctionType((ValType.i32,), tuple()),
            FunctionType(tuple(), (ValType.i32,)),
            False,
        ),
    ),
)
def test_function_type_equality(function_type_a, function_type_b, expected):
    actual = function_type_a == function_type_b
    assert actual is expected
