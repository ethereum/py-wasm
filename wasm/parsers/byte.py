from typing import IO

import numpy

from wasm.exceptions import (
    ParseError,
)

from .size import (
    parse_size,
)


def parse_single_byte(stream: IO[bytes]) -> numpy.uint8:
    """
    Parses a single byte from the stream returning it as an 8-bit integer.
    """
    byte = stream.read(1)

    if byte:
        return numpy.uint8(byte[0])
    else:
        raise ParseError("Unexpected end of stream")


def parse_bytes(stream: IO[bytes]) -> bytes:
    """
    Parses a vector of bytes.
    """
    size = parse_size(stream)
    data = stream.read(size)

    if len(data) != size:
        raise ParseError(
            f"Error parsing raw bytes.  Expected bytestream of size {size}. "
            f"Parsed stream is of size {len(data)}"
        )
    return data
