from typing import (
    List,
    NamedTuple,
    Union,
)

from .function import (
    HostFunction,
)
from .globals import (
    GlobalInstance,
)
from .memory import (
    MemoryInstance,
)
from .module import (
    FunctionInstance,
)
from .table import (
    TableInstance,
)


class Store(NamedTuple):
    funcs: List[Union[FunctionInstance, HostFunction]]
    mems: List[MemoryInstance]
    tables: List[TableInstance]
    globals: List[GlobalInstance]
