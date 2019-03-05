from typing import (
    IO,
    Tuple,
)

from wasm.datatypes import (
    ValType,
)
from wasm.exceptions import (
    ParseError,
)

from .byte import (
    parse_single_byte,
)


def parse_blocktype(stream: IO[bytes]) -> Tuple[ValType, ...]:
    """
    Parse a 'blocktype' value for one of the BLOCK/LOOP/IF instructions.
    """
    byte = parse_single_byte(stream)
    if byte == 0x40:
        return tuple()

    try:
        valtype = ValType.from_byte(byte)
    except ValueError as err:
        raise ParseError(
            f"Invalid byte while parsing mut.  Got '{hex(byte)}: {str(err)}"
        )

    return (valtype,)
