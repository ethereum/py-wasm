import numpy
import pytest

from wasm import (
    constants,
)
from wasm.datatypes import (
    ValType,
)
from wasm.exceptions import (
    ValidationError,
)


@pytest.mark.parametrize(
    'valtype,arg,is_valid',
    (
        # i32
        (ValType.i32, constants.UINT32_MIN, True),
        (ValType.i32, constants.UINT32_MAX, True),
        (ValType.i32, constants.UINT32_FLOOR, False),
        (ValType.i32, constants.UINT32_CEIL, False),
        # i64
        (ValType.i64, constants.UINT64_MIN, True),
        (ValType.i64, constants.UINT64_MAX, True),
        (ValType.i64, constants.UINT64_FLOOR, False),
        (ValType.i64, constants.UINT64_CEIL, False),
        # f32
        (ValType.f32, constants.FLOAT32_MIN, True),
        (ValType.f32, constants.FLOAT32_MAX, True),
        (ValType.f32, -1 * 2**128, False),
        (ValType.f32, 2**128, False),
        # f64
        (ValType.f64, constants.FLOAT64_MIN, True),
        (ValType.f64, constants.FLOAT64_MAX, True),
        (ValType.f64, -1 * 2**1024, False),
        (ValType.f64, 2**1024, False),
        # inf
        (ValType.f32, numpy.float32('inf'), True),
        (ValType.f32, numpy.float32('-inf'), True),
        (ValType.f64, numpy.float64('inf'), True),
        (ValType.f64, numpy.float64('-inf'), True),
        # nan
        (ValType.f32, numpy.float32('nan'), True),
        (ValType.f32, numpy.float32('-nan'), True),
        (ValType.f64, numpy.float64('nan'), True),
        (ValType.f64, numpy.float64('-nan'), True),
    ),
)
def test_valtype_validate_argument(valtype, arg, is_valid):
    if is_valid:
        valtype.validate_arg(arg)
    else:
        with pytest.raises(ValidationError):
            valtype.validate_arg(arg)
