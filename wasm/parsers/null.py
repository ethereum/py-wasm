from typing import IO

from wasm.exceptions import (
    ParseError,
)


def parse_null_byte(stream: IO[bytes]) -> None:
    """
    Consume a single null byte from the stream

    Raise a ParseError if the stream is empty or if the consumed byte is not
    0x00
    """
    byte = stream.read(1)
    if byte == b'\x00':
        return
    elif byte:
        raise ParseError(f"Expected 0x00 but got {hex(byte[0])}")
    else:
        raise ParseError("Unexpected end of stream")
