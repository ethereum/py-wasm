import io

import pytest

from wasm.binary.leb128 import (
    parse_signed_leb128,
    parse_unsigned_leb128,
)


@pytest.mark.parametrize(
    'value,expected',
    (
        (b'\x00', 0),
        (b'\xe5\x8e\x26', 624485),
    ),
)
def test_parse_unsigned_leb128(value, expected):
    actual = parse_unsigned_leb128(io.BytesIO(value))
    assert actual == expected


@pytest.mark.parametrize(
    'value,expected',
    (
        (b'\x00', 0),
        (b'\x9b\xf1\x59', -624485),
    ),
)
def test_parse_signed_leb128(value, expected):
    actual = parse_signed_leb128(io.BytesIO(value))
    assert actual == expected
