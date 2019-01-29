import enum

from wasm._utils.interned import (
    Interned,
)
from wasm.datatypes import (
    GlobalIdx,
    LocalIdx,
)
from wasm.opcodes import (
    BinaryOpcode,
)

from .base import (
    register,
)


@register
class LocalAction(enum.Enum):
    get = 0x20
    set = 0x21
    tee = 0x22


@register
class LocalOp(Interned):
    def __init__(self,
                 opcode: BinaryOpcode,
                 action: LocalAction,
                 local_idx: LocalIdx) -> None:
        self.opcode = opcode
        self.action = action
        self.local_idx = local_idx

    def __str__(self) -> str:
        return self.opcode.text

    @classmethod
    def from_opcode(cls,
                    opcode: BinaryOpcode,
                    local_idx: LocalIdx) -> 'LocalOp':
        if opcode is BinaryOpcode.GET_LOCAL:
            return cls(opcode, LocalAction.get, local_idx)
        elif opcode is BinaryOpcode.SET_LOCAL:
            return cls(opcode, LocalAction.set, local_idx)
        elif opcode is BinaryOpcode.TEE_LOCAL:
            return cls(opcode, LocalAction.tee, local_idx)
        else:
            raise Exception(f"Invariant: got unknown opcode {opcode}")


class GlobalAction(enum.Enum):
    get = 0x23
    set = 0x24


@register
class GlobalOp(Interned):
    def __init__(self,
                 opcode: BinaryOpcode,
                 action: GlobalAction,
                 global_idx: GlobalIdx) -> None:
        self.opcode = opcode
        self.action = action
        self.global_idx = global_idx

    def __str__(self) -> str:
        return self.opcode.text

    @classmethod
    def from_opcode(cls,
                    opcode: BinaryOpcode,
                    global_idx: GlobalIdx) -> 'GlobalOp':
        if opcode is BinaryOpcode.GET_GLOBAL:
            return cls(opcode, GlobalAction.get, global_idx)
        elif opcode is BinaryOpcode.SET_GLOBAL:
            return cls(opcode, GlobalAction.set, global_idx)
        else:
            raise Exception(f"Invariant: got unknown opcode {opcode}")
