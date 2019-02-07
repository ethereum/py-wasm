from typing import IO

from wasm.datatypes import (
    Mutability,
)
from wasm.exceptions import (
    MalformedModule,
)

from .byte import (
    parse_single_byte,
)


def parse_mut(stream: IO[bytes]) -> Mutability:
    byte = parse_single_byte(stream)

    try:
        return Mutability.from_byte(byte)
    except ValueError as err:
        raise MalformedModule(
            f"Invalid byte while parsing mut.  Got '{hex(byte)}: {str(err)}"
        )
