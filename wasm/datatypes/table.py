from typing import (
    List,
    NamedTuple,
    Optional,
    Type,
)

import numpy

from .addresses import (
    FunctionAddress,
)
from .limits import (
    Limits,
)


class TableType(NamedTuple):
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#table-types%E2%91%A0
    """
    limits: Limits
    elem_type: Type[FunctionAddress]


class Table(NamedTuple):
    type: TableType


class TableInstance(NamedTuple):
    elem: List[Optional[FunctionAddress]]
    max: Optional[numpy.uint32]
