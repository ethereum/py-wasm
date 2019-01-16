import math

import pytest

from wasm.tools.fixtures.numeric import (
    int_to_float,
)


@pytest.mark.parametrize(
    'num_bits,value,expected',
    (
        # 32-bit
        (32, 0, 0.0),
        (32, 1, 1.401298464324817e-45),
        (32, 1120403456, 100.0),
        (32, 2**32 - 1, math.nan),
        (32, 1325400064, 2147483648),  # float(2**31 - 1)
        # 64-bit
        (64, 0, 0.0),
        (64, 1, 5e-324),
        (64, 2**64 - 1, math.nan),
        (64, 4636737291354636288, 100.0),
    ),
)
def test_int_to_float(num_bits, value, expected):
    actual = int_to_float(num_bits, value)
    assert isinstance(actual, float)

    if math.isnan(expected):
        assert math.isnan(actual)
    else:
        assert actual == expected


@pytest.mark.parametrize(
    'num_bits,value',
    (
        (32, -1),
        (32, 2**32),
        (64, -1),
        (64, 2**64),
    )
)
def test_int_to_float_bounds(num_bits, value):
    with pytest.raises(OverflowError):
        int_to_float(num_bits, value)
