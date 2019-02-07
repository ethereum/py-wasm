from typing import IO

from wasm.datatypes import (
    DataSegment,
)

from .byte import (
    parse_bytes,
)
from .expressions import (
    parse_expression,
)
from .indices import (
    parse_memory_idx,
)


def parse_data_segment(stream: IO[bytes]) -> DataSegment:
    memory_idx = parse_memory_idx(stream)
    offset = parse_expression(stream)
    init = parse_bytes(stream)
    return DataSegment(memory_idx, offset, init)
