from typing import (
    NamedTuple,
    Optional,
    Tuple,
    Union,
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


class UnresolvedTypeIdx(NamedTuple):
    name: str


class UnresolvedCallIndirect(NamedTuple):
    type_idx: Union[UnresolvedFunctionType, UnresolvedTypeIdx]


class UnresolvedFunctionIdx(NamedTuple):
    name: str


class UnresolvedCall(NamedTuple):
    func_idx: UnresolvedFunctionIdx
