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
