from typing import (
    NamedTuple,
    Tuple,
)

from wasm.typing import (
    Expression,
)

from .indices import (
    FuncIdx,
    TableIdx,
)


class ElementSegment(NamedTuple):
    table_idx: TableIdx
    offset: Expression
    init: Tuple[FuncIdx, ]
