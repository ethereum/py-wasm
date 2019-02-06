import io

import pytest

from wasm.datatypes import (
    ValType,
)
from wasm.exceptions import (
    ParseError,
)
from wasm.parsers.blocks import (
    parse_blocktype,
)


@pytest.mark.parametrize(
    'raw,expected',
    (
        (b'\x40', tuple()),
        (b'\x7f', (ValType.i32,)),
        (b'\x7e', (ValType.i64,)),
        (b'\x7d', (ValType.f32,)),
        (b'\x7c', (ValType.f64,)),
    ),
)
def test_parse_blocktype(raw, expected):
    actual = parse_blocktype(io.BytesIO(raw))
    assert actual == expected


def test_parse_blocktype_invalid():
    with pytest.raises(ParseError):
        parse_blocktype(io.BytesIO(b'\x00'))
