from typing import IO

from wasm.exceptions import (
    MalformedModule,
    ParseError,
)


def parse_null_byte(stream: IO[bytes]) -> None:
    byte = stream.read(1)
    if byte == b'\x00':
        return
    elif byte:
        raise MalformedModule(f"TODO: expected 0x00 but got {hex(byte[0])}")
    else:
        raise ParseError("Unexpected end of stream")
