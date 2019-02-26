from typing import (
    Any,
    Tuple,
)

import numpy

from wasm import (
    constants,
)
from wasm.typing import (
    Float,
    UnsignedInt,
)

# the mantissa bits
MANTISSA_64_MASK = numpy.uint64(2**constants.F64_SIGNIF - 1)
MANTISSA_32_MASK = numpy.uint32(2**constants.F32_SIGNIF - 1)

# the expon bits
EXPONENT_64_MASK = numpy.uint64(2**constants.F64_EXPON - 1 << constants.F64_SIGNIF)
EXPONENT_32_MASK = numpy.uint32(2**constants.F32_EXPON - 1 << constants.F32_SIGNIF)

# most significant bit
SIGN_64_MASK = numpy.uint64(2**63)
SIGN_32_MASK = numpy.uint32(2**31)

_CHECK_64_AND_MASK = MANTISSA_64_MASK & EXPONENT_64_MASK & SIGN_64_MASK
_CHECK_32_AND_MASK = MANTISSA_32_MASK & EXPONENT_32_MASK & SIGN_32_MASK
_CHECK_64_OR_MASK = MANTISSA_64_MASK | EXPONENT_64_MASK | SIGN_64_MASK
_CHECK_32_OR_MASK = MANTISSA_32_MASK | EXPONENT_32_MASK | SIGN_32_MASK


assert _CHECK_64_AND_MASK == 0
assert _CHECK_32_AND_MASK == 0
assert _CHECK_64_OR_MASK == numpy.uint64(2**64 - 1)
assert _CHECK_32_OR_MASK == numpy.uint32(2**32 - 1)


def _decompose_float32(value: numpy.float32) -> Tuple[numpy.uint32, numpy.uint32, numpy.uint32]:
    as_uint32 = numpy.frombuffer(value.data, numpy.uint32)[0]
    sign = numpy.uint32(bool(as_uint32 & SIGN_32_MASK))
    exponent = numpy.uint32(int(as_uint32 & EXPONENT_32_MASK) >> constants.F32_SIGNIF)
    mantissa = as_uint32 & MANTISSA_32_MASK

    return (sign, exponent, mantissa)


def _decompose_float64(value: numpy.float64) -> Tuple[numpy.uint64, numpy.uint64, numpy.uint64]:
    as_uint64 = numpy.frombuffer(value.data, numpy.uint64)[0]
    sign = numpy.uint64(bool(as_uint64 & SIGN_64_MASK))
    exponent = numpy.uint64(int(as_uint64 & EXPONENT_64_MASK) >> constants.F64_SIGNIF)
    mantissa = as_uint64 & MANTISSA_64_MASK

    return (sign, exponent, mantissa)


def decompose_float(value: Float,
                    ) -> Tuple[UnsignedInt, UnsignedInt, UnsignedInt]:
    if isinstance(value, numpy.float64):
        return _decompose_float64(value)
    elif isinstance(value, numpy.float32):
        return _decompose_float32(value)
    else:
        raise TypeError(f"Invalid type: {type(value)}")


def compose_float64(sign: UnsignedInt,
                    exponent: UnsignedInt,
                    mantissa: UnsignedInt) -> numpy.float64:
    as_uint64 = numpy.uint64(
        (int(sign) << 63) | (int(exponent) << constants.F64_SIGNIF) | int(mantissa)
    )
    return numpy.frombuffer(as_uint64.data, numpy.float64)[0]


def compose_float32(sign: UnsignedInt,
                    exponent: UnsignedInt,
                    mantissa: UnsignedInt) -> numpy.float32:
    as_uint32 = numpy.uint32(
        (int(sign) << 31) | (int(exponent) << constants.F32_SIGNIF) | int(mantissa)
    )
    return numpy.frombuffer(as_uint32.data, numpy.float32)[0]


def is_canonical_nan(value: Any) -> bool:
    _, _, mantissa = decompose_float(value)

    if not numpy.isnan(value):
        return False
    elif isinstance(value, numpy.float64):
        return bool(mantissa == constants.F64_CANON_N)
    elif isinstance(value, numpy.float32):
        return bool(mantissa == constants.F32_CANON_N)
    else:
        raise TypeError(f"Invalid type: {type(value)}")


# runtime check since the actual value *might* differ on different platforms.
assert is_canonical_nan(constants.F32_CANON_NAN)
assert is_canonical_nan(constants.F64_CANON_NAN)


def is_arithmetic_nan(value: Any) -> bool:
    _, _, mantissa = decompose_float(value)

    if not numpy.isnan(value):
        return False
    elif isinstance(value, numpy.float64):
        return bool(mantissa >= constants.F64_CANON_N)
    elif isinstance(value, numpy.float32):
        return bool(mantissa >= constants.F32_CANON_N)
    else:
        raise TypeError(f"Invalid type: {type(value)}")
