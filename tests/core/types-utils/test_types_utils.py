import itertools

import pytest

from wasm import (
    constants,
)
from wasm._utils.types import (
    get_bit_size,
    get_float_type,
    get_integer_type,
    is_float_type,
    is_integer_type,
)


@pytest.mark.parametrize(
    'get_X_type,bit_size',
    itertools.product(
        [get_float_type, get_integer_type],
        (0, 31, 33, 63, 65),
    ),
)
def test_get_X_type_invalid_bit_size(get_X_type, bit_size):
    with pytest.raises(ValueError):
        get_X_type(bit_size)


@pytest.mark.parametrize(
    'value,expected',
    (
        (32, constants.FLOAT32),
        (64, constants.FLOAT64),
    )
)
def test_get_float_type(value, expected):
    actual = get_float_type(value)
    # using `is` comparison here to ensure that we are using the same object,
    # not just an equal string.
    assert actual is expected


@pytest.mark.parametrize(
    'value,expected',
    (
        (32, constants.INT32),
        (64, constants.INT64),
    )
)
def test_get_integer_type(value, expected):
    actual = get_integer_type(value)
    # using `is` comparison here to ensure that we are using the same object,
    # not just an equal string.
    assert actual is expected


@pytest.mark.parametrize(
    'value,expected',
    (
        # good
        ('f32', True),
        (constants.FLOAT32, True),
        ('f64', True),
        (constants.FLOAT64, True),
        # bad
        ('i32', False),
        ('i64', False),
        ('F32', False),
        ('F64', False),
        (b'F32', False),
        (b'F64', False),
        (b'f32', False),
        (b'f64', False),
        ('something-random', False),
    )
)
def test_is_float_type(value, expected):
    actual = is_float_type(value)
    assert actual is expected


@pytest.mark.parametrize(
    'value,expected',
    (
        # good
        ('i32', True),
        (constants.INT32, True),
        ('i64', True),
        (constants.INT64, True),
        # bad
        ('f32', False),
        ('f64', False),
        ('I32', False),
        ('I64', False),
        (b'I32', False),
        (b'I64', False),
        (b'i32', False),
        (b'i64', False),
        ('something-random', False),
    )
)
def test_is_integer_type(value, expected):
    actual = is_integer_type(value)
    assert actual is expected


@pytest.mark.parametrize(
    'value,expected',
    (
        (constants.INT32, 32),
        (constants.INT64, 64),
        (constants.FLOAT32, 32),
        (constants.FLOAT64, 64),
    ),
)
def test_get_bit_size(value, expected):
    actual = get_bit_size(value)
    assert actual == expected


@pytest.mark.parametrize(
    'value',
    (
        'F32',
        'F64',
        'I32',
        'I64',
        b'F32',
        b'F64',
        b'I32',
        b'I64',
        b'f32',
        b'f64',
        b'i32',
        b'i64',
        'some-random-value',
    ),
)
def test_get_bit_size_invalid_values(value):
    with pytest.raises(ValueError):
        get_bit_size(value)
