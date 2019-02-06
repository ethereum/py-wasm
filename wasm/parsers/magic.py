import io
from typing import (
    Tuple,
)

from wasm.exceptions import (
    MalformedModule,
)
from wasm.typing import (
    UInt8,
)

from .byte import (
    parse_single_byte,
)

MAGIC = (UInt8(0x00), UInt8(0x61), UInt8(0x73), UInt8(0x6D))


def parse_magic(stream: io.BytesIO) -> Tuple[UInt8, UInt8, UInt8, UInt8]:
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
