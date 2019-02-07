from typing import IO

from wasm.datatypes import (
    ValType,
)
from wasm.exceptions import (
    MalformedModule,
)

from .byte import (
    parse_single_byte,
)


def parse_valtype(stream: IO[bytes]) -> ValType:
    byte = parse_single_byte(stream)

    try:
        return ValType.from_byte(byte)
    except ValueError as err:
        raise MalformedModule(
            f"Invalid byte while parsing valtype.  Got '{hex(byte)}: {str(err)}"
        )
