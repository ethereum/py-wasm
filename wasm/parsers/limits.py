from typing import IO

from wasm.datatypes import (
    Limits,
)
from wasm.exceptions import (
    InvalidModule,
)

from .byte import (
    parse_single_byte,
)
from .integers import (
    parse_u32,
)


def parse_limits(stream: IO[bytes]) -> Limits:
    """
    Parser for the Limits type
    """
    flag = parse_single_byte(stream)

    if flag == 0x0:
        min_ = parse_u32(stream)
        return Limits(min_, None)
    elif flag == 0x01:
        min_ = parse_u32(stream)
        max_ = parse_u32(stream)
        return Limits(min_, max_)
    else:
        raise InvalidModule(
            "Invalid starting byte for limits type.  Expected starting byte to "
            f"be one of 0x00 or 0x01: Got {hex(flag)}"
        )
