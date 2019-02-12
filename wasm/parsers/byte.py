from typing import IO

from wasm.exceptions import (
    ParseError,
)
from wasm.typing import (
    UInt8,
)

from .size import (
    parse_size,
)


def parse_single_byte(stream: IO[bytes]) -> UInt8:
    byte = stream.read(1)

    if byte:
        return UInt8(byte[0])
    else:
        raise ParseError("Unexpected end of stream")


def parse_bytes(stream: IO[bytes]) -> bytes:
    size = parse_size(stream)
    data = stream.read(size)

    if len(data) != size:
        raise ParseError(
            f"Error parsing raw bytes.  Expected bytestream of size {size}. "
            f"Parsed stream is of size {len(data)}"
        )
    return data
