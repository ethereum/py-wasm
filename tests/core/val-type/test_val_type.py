import itertools

import pytest

from wasm.datatypes import (
    BitSize,
    ValType,
)


@pytest.mark.parametrize(
    'get_X_type,bit_size',
    itertools.product(
        [ValType.get_integer_type, ValType.get_float_type],
        (0, 31, 33, 63, 65, BitSize.b8, BitSize.b16),
    ),
)
def test_get_X_type_invalid_bit_size(get_X_type, bit_size):
    with pytest.raises(ValueError):
        get_X_type(bit_size)


@pytest.mark.parametrize(
    'value,expected',
    (
        (BitSize.b32, ValType.f32),
        (BitSize.b64, ValType.f64),
    )
)
def test_get_float_type(value, expected):
    actual = ValType.get_float_type(value)
    # using `is` comparison here to ensure that we are using the same object,
    # not just an equal string.
    assert actual is expected


@pytest.mark.parametrize(
    'value,expected',
    (
        (BitSize.b32, ValType.i32),
        (BitSize.b64, ValType.i64),
    )
)
def test_get_integer_type(value, expected):
    actual = ValType.get_integer_type(value)
    # using `is` comparison here to ensure that we are using the same object,
    # not just an equal string.
    assert actual is expected


@pytest.mark.parametrize(
    'value,expected',
    (
        (ValType.f32, True),
        (ValType.f64, True),
        (ValType.i32, False),
        (ValType.i64, False),
    )
)
def test_is_float_type(value, expected):
    assert value.is_float_type is expected


@pytest.mark.parametrize(
    'value,expected',
    (
        (ValType.f32, False),
        (ValType.f64, False),
        (ValType.i32, True),
        (ValType.i64, True),
    )
)
def test_is_integer_type(value, expected):
    assert value.is_integer_type is expected


@pytest.mark.parametrize(
    'value,expected',
    (
        (ValType.f32, BitSize.b32),
        (ValType.f64, BitSize.b64),
        (ValType.i32, BitSize.b32),
        (ValType.i64, BitSize.b64),
    ),
)
def test_get_bit_size(value, expected):
    assert value.bit_size == expected
