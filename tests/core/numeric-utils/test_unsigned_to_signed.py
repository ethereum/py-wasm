from hypothesis import (
    given,
    strategies as st,
)
import pytest

from wasm import (
    constants,
)
from wasm._utils.numeric import (
    u32_to_s32,
    u64_to_s64,
)


@pytest.mark.parametrize(
    'convert_fn,value,expected',
    (
        (u32_to_s32, 0, 0),
        (u64_to_s64, 0, 0),
        (u32_to_s32, 1, 1),
        (u64_to_s64, 1, 1),
        (u32_to_s32, constants.UINT32_MAX, -1),
        (u64_to_s64, constants.UINT64_MAX, -1),
        (u32_to_s32, constants.SINT32_CEIL, constants.SINT32_MIN),
        (u64_to_s64, constants.SINT64_CEIL, constants.SINT64_MIN),
        (u32_to_s32, constants.SINT32_MAX, constants.SINT32_MAX),
        (u64_to_s64, constants.SINT64_MAX, constants.SINT64_MAX),
    ),
)
def test_unsigned_to_signed(convert_fn, value, expected):
    actual = convert_fn(value)
    assert actual == expected


@given(
    value=st.integers(
        min_value=0,
        max_value=constants.UINT32_MAX,
    ),
)
def test_unsigned32_to_signed32_fuzz(value):
    actual = u32_to_s32(value)
    if value > constants.SINT32_MAX:
        assert actual < 0
    else:
        assert actual == value


@given(
    value=st.integers(
        min_value=0,
        max_value=constants.UINT64_MAX,
    ),
)
def test_unsigned64_to_signed64_fuzz(value):
    actual = u64_to_s64(value)
    if value > constants.SINT64_MAX:
        assert actual < 0
    else:
        assert actual == value
