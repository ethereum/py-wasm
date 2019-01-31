import pytest

from wasm import (
    constants,
)
from wasm.datatypes import (
    Limits,
)
from wasm.exceptions import (
    ValidationError,
)
from wasm.validation import (
    validate_limits,
)


@pytest.mark.parametrize(
    'limits,upper_bound,expected',
    (
        (Limits(0, None), 10, None),
        (Limits(0, 10), 10, None),
        (Limits(-1, 10), 10, "Limits.min is negative"),
        (Limits(0, 11), 10, "Limits.max exceeds upper bound"),
        (Limits(11, 20), 10, "Limits.min exceeds upper bound"),
        (Limits(10, 9), 10, "Limits.min exceeds Limits.max"),
        (
            Limits(0, constants.UINT32_CEIL),
            constants.UINT32_CEIL,
            "Limits.max is outside of u32 range"
        ),
        (
            Limits(constants.UINT32_CEIL, constants.UINT32_CEIL + 1),
            constants.UINT32_CEIL + 1,
            "Limits.min is outside of u32 range"
        ),
    ),
)
def test_validate_limits(limits, upper_bound, expected):
    if expected is None:
        # should be valid
        validate_limits(limits, upper_bound)
    else:
        with pytest.raises(ValidationError, match=expected):
            validate_limits(limits, upper_bound)
