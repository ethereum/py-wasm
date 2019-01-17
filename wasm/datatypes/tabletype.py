from typing import (
    NamedTuple,
    Type,
)

from .limits import (
    Limits,
)


class FuncType(NamedTuple):
    """
    Placeholder until function types get their own formal data structure.
    """
    pass


class TableType(NamedTuple):
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#table-types%E2%91%A0
    """
    limits: Limits
    elem_type: Type[FuncType]
