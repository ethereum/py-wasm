from hypothesis import (
    given,
    strategies as st,
)
import pytest

from wasm import (
    constants,
)
from wasm._utils.numeric import (
    s32_to_u32,
    s64_to_u64,
)


@pytest.mark.parametrize(
    'convert_fn,value,expected',
    (
        (s32_to_u32, 0, 0),
        (s64_to_u64, 0, 0),
        (s32_to_u32, 1, 1),
        (s64_to_u64, 1, 1),
        (s32_to_u32, constants.SINT32_MIN, constants.SINT32_CEIL),
        (s64_to_u64, constants.SINT64_MIN, constants.SINT64_CEIL),
    ),
)
def test_signed_to_unsigned(convert_fn, value, expected):
    actual = convert_fn(value)
    assert actual == expected


@given(
    value=st.integers(
        min_value=constants.SINT32_MIN,
        max_value=constants.SINT32_MAX,
    ),
)
def test_signed32_to_unsigned32_fuzz(value):
    actual = s32_to_u32(value)
    if value >= 0:
        assert actual == value
    else:
        assert actual >= 0


@given(
    value=st.integers(
        min_value=constants.SINT64_MIN,
        max_value=constants.SINT64_MAX,
    ),
)
def test_signed64_to_unsigned64_fuzz(value):
    actual = s64_to_u64(value)
    if value >= 0:
        assert actual == value
    else:
        assert actual >= 0
