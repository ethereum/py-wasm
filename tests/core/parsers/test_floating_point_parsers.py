import io
import math
import struct

from hypothesis import (
    given,
    strategies as st,
)
import pytest

from wasm.parsers.floats import (
    parse_f32,
    parse_f64,
)


@pytest.mark.parametrize(
    'encoded,expected',
    (
        # from a spec test failure while refactoring the library.
        (b'\x00\x00\xc0\x7f', math.nan),
    ),
)
def test_parse_f32(encoded, expected):
    actual = parse_f32(io.BytesIO(encoded))

    if math.isnan(expected):
        assert math.isnan(actual)
    elif math.isinf(expected):
        assert math.isinf(actual)
    else:
        assert actual == expected


@given(
    value=st.floats(width=32),
)
def test_parse_f32_fuzz(value):
    encoded = struct.pack('<f', value)
    result = parse_f32(io.BytesIO(encoded))

    if math.isnan(value):
        assert math.isnan(result)
    elif math.isinf(value):
        assert math.isinf(result)
    else:
        assert result == value


@given(
    value=st.floats(width=64),
)
def test_parse_f64_fuzz(value):
    encoded = struct.pack('<d', value)
    result = parse_f64(io.BytesIO(encoded))

    if math.isnan(value):
        assert math.isnan(result)
    elif math.isinf(value):
        assert math.isinf(result)
    else:
        assert result == value
