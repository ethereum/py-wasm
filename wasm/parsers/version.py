from typing import (
    IO,
    Tuple,
)

import numpy

from wasm import (
    constants,
)
from wasm.exceptions import (
    ParseError,
)

from .byte import (
    parse_single_byte,
)

KNOWN_VERSIONS = {
    constants.VERSION_1,
}


def parse_version(stream: IO[bytes]) -> Tuple[numpy.uint8, numpy.uint8, numpy.uint8, numpy.uint8]:
    """
    Parser for the version portion of a binary encoded WebAssembly module
    https://webassembly.github.io/spec/core/bikeshed/index.html#binary-version
    """
    actual = (
        parse_single_byte(stream),
        parse_single_byte(stream),
        parse_single_byte(stream),
        parse_single_byte(stream),
    )
    if actual not in KNOWN_VERSIONS:
        raise ParseError(
            f"Unknown version. Got: "
            f"{tuple(hex(byte) for byte in actual)}"
        )
    return actual
