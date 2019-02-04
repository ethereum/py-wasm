import pytest

from wasm.datatypes import (
    GlobalType,
    Mutability,
    ValType,
)


@pytest.mark.parametrize(
    'global_type_a,global_type_b,expected',
    (
        (
            GlobalType(Mutability.const, ValType.i32),
            GlobalType(Mutability.const, ValType.i32),
            True,
        ),
        (
            GlobalType(Mutability.var, ValType.i32),
            GlobalType(Mutability.var, ValType.i32),
            True,
        ),
        (
            GlobalType(Mutability.const, ValType.i32),
            GlobalType(Mutability.var, ValType.i32),
            False,
        ),
        (
            GlobalType(Mutability.const, ValType.i32),
            GlobalType(Mutability.const, ValType.i64),
            False,
        ),
    ),
)
def test_global_type_equality(global_type_a, global_type_b, expected):
    actual = global_type_a == global_type_b
    assert actual is expected
