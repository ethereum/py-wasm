from hypothesis import (
    given,
    strategies as st,
)

from wasm import (
    constants,
)
from wasm._utils.numeric import (
    s32_to_u32,
    s64_to_u64,
    u32_to_s32,
    u64_to_s64,
)


@given(
    value=st.integers(
        min_value=0,
        max_value=constants.UINT32_MAX,
    ),
)
def test_unsigned32_round_trip(value):
    actual = s32_to_u32(u32_to_s32(value))
    assert actual == value


@given(
    value=st.integers(
        min_value=0,
        max_value=constants.UINT64_MAX,
    ),
)
def test_unsigned64_round_trip(value):
    actual = s64_to_u64(u64_to_s64(value))
    assert actual == value


@given(
    value=st.integers(
        min_value=constants.SINT32_MIN,
        max_value=constants.SINT32_MAX,
    ),
)
def test_signed32_round_trip(value):
    actual = u32_to_s32(s32_to_u32(value))
    assert actual == value


@given(
    value=st.integers(
        min_value=constants.SINT64_MIN,
        max_value=constants.SINT64_MAX,
    ),
)
def test_signed64_round_trip(value):
    actual = u64_to_s64(s64_to_u64(value))
    assert actual == value
