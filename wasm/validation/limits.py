from wasm import (
    constants,
)
from wasm.datatypes import (
    Limits,
)
from wasm.exceptions import (
    ValidationError,
)


def validate_limits(limits: Limits, upper_bound: int) -> None:
    """
    Validate a Limits object

    https://webassembly.github.io/spec/core/bikeshed/index.html#limits%E2%91%A2
    """
    if limits.min > constants.UINT32_MAX:
        raise ValidationError("Limits.min is outside of u32 range: Got {limits.min}")
    elif limits.min < 0:
        raise ValidationError("Limits.min is negative: Got {limits.min}")
    elif limits.min > upper_bound:
        raise ValidationError(f"Limits.min exceeds upper bound: {limits.min} > {upper_bound}")
    elif limits.max is not None:
        if limits.max > constants.UINT32_MAX:
            raise ValidationError("Limits.max is outside of u32 range: Got {limits.max}")
        elif limits.max > upper_bound:
            raise ValidationError(f"Limits.max exceeds upper bound: {limits.max} > {upper_bound}")
        elif limits.min > limits.max:
            raise ValidationError(
                f"Limits.min exceeds Limits.max: {limits.min} > "
                f"{limits.max}"
            )
