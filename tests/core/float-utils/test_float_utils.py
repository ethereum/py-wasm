from hypothesis import (
    given,
    strategies as st,
)
import numpy
import pytest

from wasm import (
    constants,
)
from wasm._utils.float import (
    compose_float32,
    compose_float64,
    decompose_float,
    is_arithmetic_nan,
    is_canonical_nan,
)


@pytest.mark.parametrize(
    'value,expected',
    (
        (numpy.float32('nan'), (0, 2**constants.F32_EXPON - 1, constants.F32_CANON_N)),
    ),
)
def test_decompose_float(value, expected):
    e_sign, e_exponent, e_mantissa = expected
    a_sign, a_exponent, a_mantissa = decompose_float(value)

    assert a_sign == e_sign
    assert a_exponent == e_exponent
    assert a_mantissa == e_mantissa


@st.composite
def f32_strat(draw, encoded=st.binary(min_size=4, max_size=4)):
    raw_bytes = draw(encoded)
    return numpy.frombuffer(raw_bytes, numpy.float32)[0]


@st.composite
def f64_strat(draw, encoded=st.binary(min_size=8, max_size=8)):
    raw_bytes = draw(encoded)
    return numpy.frombuffer(raw_bytes, numpy.float32)[0]


@given(value=st.one_of(f32_strat(), f64_strat()))
def test_decompose_to_compose_round_trip(value):
    if isinstance(value, numpy.float32):
        compose_fn = compose_float32
    elif isinstance(value, numpy.float64):
        compose_fn = compose_float64
    else:
        assert False, "Unreachable"

    sign, exponent, mantissa = decompose_float(value)
    result = compose_fn(sign, exponent, mantissa)
    assert result.tobytes() == value.tobytes()


F32_C_SIGN, F32_C_EXPONENT, F32_C_MANTISSA = decompose_float(constants.F32_CANON_NAN)
F64_C_SIGN, F64_C_EXPONENT, F64_C_MANTISSA = decompose_float(constants.F64_CANON_NAN)


@pytest.mark.parametrize(
    'value,expected',
    (
        (constants.F32_CANON_NAN, True),
        (constants.F64_CANON_NAN, True),
        (compose_float32(F32_C_SIGN, F32_C_EXPONENT, F32_C_MANTISSA + 1), False),
        (compose_float64(F64_C_SIGN, F64_C_EXPONENT, F64_C_MANTISSA + 1), False),
        (compose_float32(F32_C_SIGN, F32_C_EXPONENT, F32_C_MANTISSA - 1), False),
        (compose_float64(F64_C_SIGN, F64_C_EXPONENT, F64_C_MANTISSA - 1), False),
    ),
)
def test_is_canonical_nan(value, expected):
    actual = is_canonical_nan(value)
    if actual is not expected:
        sign, exponent, mantissa = decompose_float(value)

        raise AssertionError(
            f"NAN is not canonical: sign:{int(sign)}  exponent:{int(exponent)}  "
            f"mantissa:{int(mantissa)}"
        )


@pytest.mark.parametrize(
    'value,expected',
    (
        (constants.F32_CANON_NAN, True),
        (constants.F64_CANON_NAN, True),
        (compose_float32(F32_C_SIGN, F32_C_EXPONENT, F32_C_MANTISSA + 1), True),
        (compose_float64(F64_C_SIGN, F64_C_EXPONENT, F64_C_MANTISSA + 1), True),
        (compose_float32(F32_C_SIGN, F32_C_EXPONENT, F32_C_MANTISSA - 1), False),
        (compose_float64(F64_C_SIGN, F64_C_EXPONENT, F64_C_MANTISSA - 1), False),
    ),
)
def test_is_arithmetic_nan(value, expected):
    actual = is_arithmetic_nan(value)
    if actual is not expected:
        sign, exponent, mantissa = decompose_float(value)

        raise AssertionError(
            f"NAN is not arithmetic: sign:{int(sign)}  exponent:{int(exponent)}  "
            f"mantissa:{int(mantissa)}"
        )
