import io

import pytest

from wasm.exceptions import (
    MalformedModule,
)
from wasm.parsers.integers import (
    parse_i32,
    parse_i64,
    parse_s32,
    parse_s64,
    parse_u32,
    parse_u64,
)


@pytest.mark.parametrize(
    'parse_fn,raw_value',
    (
        (parse_i32, b'\x80\x80\x80\x80\x80\x00'),
        (parse_s32, b'\x80\x80\x80\x80\x80\x00'),
        (parse_u32, b'\x80\x80\x80\x80\x80\x00'),
        (parse_i64, b'\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x00'),
        (parse_s64, b'\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x00'),
        (parse_u64, b'\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x00'),
    ),
)
def test_values_exceeding_byte_width(parse_fn, raw_value):
    with pytest.raises(MalformedModule, match="maximum byte width"):
        parse_fn(io.BytesIO(raw_value))


@pytest.mark.parametrize(
    'parse_fn,raw_value',
    (
        (parse_i32, b'\xff\xff\xff\xff\x0f'),
        (parse_s32, b'\xff\xff\xff\xff\x0f'),
        (parse_i64, b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\x0f'),
        (parse_s64, b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\x0f'),
    ),
)
def test_out_of_range_value(parse_fn, raw_value):
    with pytest.raises(MalformedModule, match="decoded .* is greater than"):
        parse_fn(io.BytesIO(raw_value))


@pytest.mark.parametrize(
    'parse_fn,raw_value,expected',
    (
        (parse_i32, b'\x00', 0),
        (parse_s32, b'\x00', 0),
        (parse_u32, b'\x00', 0),
        (parse_i64, b'\x00', 0),
        (parse_s64, b'\x00', 0),
        (parse_u64, b'\x00', 0),
        # from wikipedia spec (unsigned)
        (parse_i32, b'\xe5\x8e\x26', 624485),
        (parse_s32, b'\xe5\x8e\x26', 624485),
        (parse_u32, b'\xe5\x8e\x26', 624485),
        (parse_i64, b'\xe5\x8e\x26', 624485),
        (parse_s64, b'\xe5\x8e\x26', 624485),
        (parse_u64, b'\xe5\x8e\x26', 624485),
        # from wikipedia spec (signed)
        (parse_s32, b'\x9b\xf1\x59', -624485),
        (parse_s64, b'\x9b\xf1\x59', -624485),
    ),
)
def test_parseing_encoded_integer(parse_fn, raw_value, expected):
    actual = parse_fn(io.BytesIO(raw_value))
    assert actual == expected
