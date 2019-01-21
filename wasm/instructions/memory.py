import collections
import enum
from typing import (
    Optional,
)

from wasm._utils.interned import (
    Interned,
)
from wasm.datatypes import (
    BitSize,
    ValType,
)
from wasm.opcodes import (
    BinaryOpcode,
)
from wasm.typing import (
    UInt32,
)

from .base import (
    SimpleOp,
    register,
)


class MemoryArg(Interned, collections.abc.Hashable):
    def __init__(self,
                 offset: UInt32,
                 align: UInt32) -> None:
        self.offset = offset
        self.align = align

    def __hash__(self) -> int:
        return hash((self.offset, self.align))


class MemoryAction(enum.Enum):
    load = 'load'
    store = 'store'


@register
class MemoryOp(Interned):
    def __init__(self,
                 opcode: BinaryOpcode,
                 action: MemoryAction,
                 memarg: MemoryArg,
                 valtype: ValType,
                 declared_bit_size: Optional[BitSize],
                 signed: Optional[bool]) -> None:
        self.opcode = opcode
        self.action = action
        self.memarg = memarg
        self.valtype = valtype
        self.declared_bit_size = declared_bit_size
        self.signed = signed

    def __str__(self) -> str:
        return f"{self.opcode.text}[align={self.memarg.align},offset={self.memarg.offset}]"

    @property
    def memory_bit_size(self) -> BitSize:
        if self.declared_bit_size is None:
            return self.valtype.bit_size
        else:
            return self.declared_bit_size

    @classmethod
    def from_opcode(cls,
                    opcode: BinaryOpcode,
                    memarg: MemoryArg) -> 'MemoryOp':
        if opcode is BinaryOpcode.F32_LOAD:
            return cls(opcode, MemoryAction.load, memarg, ValType.f32, None, None)
        elif opcode is BinaryOpcode.F32_STORE:
            return cls(opcode, MemoryAction.store, memarg, ValType.f32, None, None)
        elif opcode is BinaryOpcode.F64_LOAD:
            return cls(opcode, MemoryAction.load, memarg, ValType.f64, None, None)
        elif opcode is BinaryOpcode.F64_STORE:
            return cls(opcode, MemoryAction.store, memarg, ValType.f64, None, None)
        elif opcode is BinaryOpcode.I32_LOAD:
            return cls(opcode, MemoryAction.load, memarg, ValType.i32, None, None)
        elif opcode is BinaryOpcode.I32_LOAD16_S:
            return cls(opcode, MemoryAction.load, memarg, ValType.i32, BitSize.b16, True)
        elif opcode is BinaryOpcode.I32_LOAD16_U:
            return cls(opcode, MemoryAction.load, memarg, ValType.i32, BitSize.b16, False)
        elif opcode is BinaryOpcode.I32_LOAD8_S:
            return cls(opcode, MemoryAction.load, memarg, ValType.i32, BitSize.b8, True)
        elif opcode is BinaryOpcode.I32_LOAD8_U:
            return cls(opcode, MemoryAction.load, memarg, ValType.i32, BitSize.b8, False)
        elif opcode is BinaryOpcode.I32_STORE:
            return cls(opcode, MemoryAction.store, memarg, ValType.i32, None, None)
        elif opcode is BinaryOpcode.I32_STORE16:
            return cls(opcode, MemoryAction.store, memarg, ValType.i32, BitSize.b16, None)
        elif opcode is BinaryOpcode.I32_STORE8:
            return cls(opcode, MemoryAction.store, memarg, ValType.i32, BitSize.b8, None)
        elif opcode is BinaryOpcode.I64_LOAD:
            return cls(opcode, MemoryAction.load, memarg, ValType.i64, None, None)
        elif opcode is BinaryOpcode.I64_LOAD16_S:
            return cls(opcode, MemoryAction.load, memarg, ValType.i64, BitSize.b16, True)
        elif opcode is BinaryOpcode.I64_LOAD16_U:
            return cls(opcode, MemoryAction.load, memarg, ValType.i64, BitSize.b16, False)
        elif opcode is BinaryOpcode.I64_LOAD32_S:
            return cls(opcode, MemoryAction.load, memarg, ValType.i64, BitSize.b32, True)
        elif opcode is BinaryOpcode.I64_LOAD32_U:
            return cls(opcode, MemoryAction.load, memarg, ValType.i64, BitSize.b32, False)
        elif opcode is BinaryOpcode.I64_LOAD8_S:
            return cls(opcode, MemoryAction.load, memarg, ValType.i64, BitSize.b8, True)
        elif opcode is BinaryOpcode.I64_LOAD8_U:
            return cls(opcode, MemoryAction.load, memarg, ValType.i64, BitSize.b8, False)
        elif opcode is BinaryOpcode.I64_STORE:
            return cls(opcode, MemoryAction.store, memarg, ValType.i64, None, None)
        elif opcode is BinaryOpcode.I64_STORE16:
            return cls(opcode, MemoryAction.store, memarg, ValType.i64, BitSize.b16, None)
        elif opcode is BinaryOpcode.I64_STORE32:
            return cls(opcode, MemoryAction.store, memarg, ValType.i64, BitSize.b32, None)
        elif opcode is BinaryOpcode.I64_STORE8:
            return cls(opcode, MemoryAction.store, memarg, ValType.i64, BitSize.b8, None)
        else:
            raise Exception(f"Invariant: got unknown opcode {opcode}")


@register
class MemorySize(SimpleOp):
    opcode = BinaryOpcode.MEMORY_SIZE


@register
class MemoryGrow(SimpleOp):
    opcode = BinaryOpcode.MEMORY_GROW
