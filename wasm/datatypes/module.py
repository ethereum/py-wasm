from typing import (
    NamedTuple,
    Optional,
    Tuple,
)

from .addresses import (
    FunctionAddress,
    GlobalAddress,
    MemoryAddress,
    TableAddress,
)
from .data_segment import (
    DataSegment,
)
from .element_segment import (
    ElementSegment,
)
from .exports import (
    Export,
    ExportInstance,
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


class ModuleInstance(NamedTuple):
    types: Tuple[FunctionType, ...]
    func_addrs: Tuple[FunctionAddress, ...]
    table_addrs: Tuple[TableAddress, ...]
    memory_addrs: Tuple[MemoryAddress, ...]
    global_addrs: Tuple[GlobalAddress, ...]
    exports: Tuple[ExportInstance, ...]


# This class is located here to prevent `mypy` from complaining about recursive
# types until they are supported.
# https://github.com/python/mypy/issues/731
class FunctionInstance(NamedTuple):
    """
    """
    type: FunctionType
    module: ModuleInstance
    code: Function
