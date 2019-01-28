from typing import (
    TYPE_CHECKING,
    NamedTuple,
    Tuple,
)

from .indices import (
    MemoryIdx,
)

if TYPE_CHECKING:
    from wasm.instructions import (  # noqa: F401
        BaseInstruction,
    )


class DataSegment(NamedTuple):
    mem_idx: MemoryIdx
    offset: Tuple['BaseInstruction', ...]
    init: bytes
