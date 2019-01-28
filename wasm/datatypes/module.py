from typing import (
    NamedTuple,
    Optional,
    Tuple,
)

from .data_segment import (
    DataSegment,
)
from .element_segment import (
    ElementSegment,
)
from .exports import (
    Export,
)
from .function import (
    Function,
    FunctionType,
    StartFunction,
)
from .globals import (
    Global,
)
from .imports import (
    Import,
)
from .memory import (
    Memory,
)
from .table import (
    Table,
)


class Module(NamedTuple):
    types: Tuple[FunctionType, ...]
    funcs: Tuple[Function, ...]
    tables: Tuple[Table, ...]
    mems: Tuple[Memory, ...]
    globals: Tuple[Global, ...]
    elem: Tuple[ElementSegment, ...]
    data: Tuple[DataSegment, ...]
    start: Optional[StartFunction]
    imports: Tuple[Import, ...]
    exports: Tuple[Export, ...]
