from typing import (
    Tuple,
)

import numpy

from wasm import (
    constants,
)
from wasm.exceptions import (
    ValidationError,
)

TVersion = Tuple[numpy.uint8, numpy.uint8, numpy.uint8, numpy.uint8]


def validate_version(version: TVersion) -> None:
    """
    Validate the parsed version string for a Web Assembly module.
    """
    if version != constants.VERSION_1:
        raise ValidationError(
            f"Unknown version. Got: "
            f"{tuple(hex(byte) for byte in version)}"
        )
