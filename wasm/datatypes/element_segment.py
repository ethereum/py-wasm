from typing import (
    TYPE_CHECKING,
    NamedTuple,
    Tuple,
)

from .indices import (
    FuncIdx,
    TableIdx,
)

if TYPE_CHECKING:
    from wasm.instructions import (  # noqa: F401
        BaseInstruction,
    )


class ElementSegment(NamedTuple):
    table_idx: TableIdx
    offset: Tuple['BaseInstruction', ...]
    init: Tuple[FuncIdx, ]
