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

KNOWN_VERSIONS = {
    (0x01, 0x00, 0x00, 0x00),
}


def parse_version(stream: io.BytesIO) -> Tuple[UInt8, UInt8, UInt8, UInt8]:
    actual = (
        parse_single_byte(stream),
        parse_single_byte(stream),
        parse_single_byte(stream),
        parse_single_byte(stream),
    )
    if actual not in KNOWN_VERSIONS:
        raise MalformedModule(
            f"Unknown version. Got: "
            f"{tuple(hex(byte) for byte in actual)}"
        )
    return actual
