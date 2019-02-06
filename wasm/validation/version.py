from typing import (
    Tuple,
)

from wasm import (
    constants,
)
from wasm.exceptions import (
    ValidationError,
)
from wasm.typing import (
    UInt8,
)


def validate_version(version: Tuple[UInt8, UInt8, UInt8, UInt8]) -> None:
    if version != constants.VERSION_1:
        raise ValidationError(
            f"Unknown version. Got: "
            f"{tuple(hex(byte) for byte in version)}"
        )
