from typing import (
    IO,
    Tuple,
)

import numpy

from wasm.exceptions import (
    MalformedModule,
)

from .byte import (
    parse_single_byte,
)

MAGIC = (numpy.uint8(0x00), numpy.uint8(0x61), numpy.uint8(0x73), numpy.uint8(0x6D))


def parse_magic(stream: IO[bytes]) -> Tuple[numpy.uint8, numpy.uint8, numpy.uint8, numpy.uint8]:
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#binary-magic
    """
    actual = (
        parse_single_byte(stream),
        parse_single_byte(stream),
        parse_single_byte(stream),
        parse_single_byte(stream),
    )
    if actual != MAGIC:
        raise MalformedModule(
            f"Invalid magic start bytes.  Got: "
            f"{tuple(hex(byte) for byte in actual)}"
        )
    return MAGIC
