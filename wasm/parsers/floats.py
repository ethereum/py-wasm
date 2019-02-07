import struct
from typing import (
    IO,
    cast,
)

from wasm.typing import (
    Float32,
    Float64,
)


def parse_f32(stream: IO[bytes]) -> Float32:
    raw_buffer = stream.read(4)
    buffer = bytes(reversed(raw_buffer))
    if len(buffer) < 4:
        raise Exception("TODO: better exception for insufficient bytes")

    value = struct.unpack(">f", buffer)[0]
    return cast(Float32, value)


def parse_f64(stream: IO[bytes]) -> Float64:
    raw_buffer = stream.read(8)
    buffer = bytes(reversed(raw_buffer))
    if len(buffer) < 8:
        raise Exception("TODO: better exception for insufficient bytes")

    value = struct.unpack(">d", buffer)[0]
    return cast(Float64, value)
