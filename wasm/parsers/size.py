from typing import IO

from .integers import (
    parse_u32,
)


def parse_size(stream: IO[bytes]) -> int:
    raw_size = parse_u32(stream)
    return int(raw_size)
