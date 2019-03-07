from typing import (
    NamedTuple,
    Optional,
)

from wasm.datatypes import (
    ValType,
)


class Local(NamedTuple):
    valtype: ValType
    name: Optional[str] = None


class Param(NamedTuple):
    valtype: ValType
    name: Optional[str] = None
