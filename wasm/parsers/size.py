from typing import (
    IO,
    cast,
)

from .integers import (
    parse_u32,
)


def parse_size(stream: IO[bytes]) -> int:
    """
    Helper function for parsing a *size* value such as the declared size of a
    section.
    """
    raw_size = parse_u32(stream)
    return cast(int, raw_size)
