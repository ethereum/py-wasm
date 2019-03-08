from typing import (
    NamedTuple,
    Optional,
    Tuple,
)

from wasm.datatypes import (
    ValType,
)
from wasm.opcodes import (
    BinaryOpcode,
)


class Local(NamedTuple):
    valtype: ValType
    name: Optional[str] = None


class Param(NamedTuple):
    valtype: ValType
    name: Optional[str] = None


class UnresolvedVariableOp(NamedTuple):
    opcode: BinaryOpcode
    name: str


class UnresolvedFunctionType(NamedTuple):
    params: Tuple[Param, ...]
    results: Tuple[ValType, ...]
