from typing import (
    NamedTuple,
)

from wasm.typing import (
    Expression,
)

from .indices import (
    MemoryIdx,
)


class DataSegment(NamedTuple):
    mem_idx: MemoryIdx
    offset: Expression
    init: bytes
