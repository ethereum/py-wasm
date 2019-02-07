from typing import IO

from wasm.datatypes import (
    Memory,
    MemoryType,
)
from wasm.instructions import (
    Instruction,
    MemoryArg,
    MemoryGrow,
    MemoryOp,
    MemorySize,
)
from wasm.opcodes import (
    BinaryOpcode,
)

from .integers import (
    parse_u32,
)
from .limits import (
    parse_limits,
)
from .null import (
    parse_null_byte,
)


def parse_memory_instruction(opcode: BinaryOpcode,
                             stream: IO[bytes]) -> Instruction:
    if opcode.is_memory_access:
        memarg = parse_memarg(stream)

        return MemoryOp.from_opcode(opcode, memarg)
    elif opcode is BinaryOpcode.MEMORY_SIZE:
        parse_null_byte(stream)
        return MemorySize()
    elif opcode is BinaryOpcode.MEMORY_GROW:
        parse_null_byte(stream)
        return MemoryGrow()
    else:
        raise Exception("Invariant")


def parse_memarg(stream: IO[bytes]) -> MemoryArg:
    align = parse_u32(stream)
    offset = parse_u32(stream)
    return MemoryArg(offset, align)


def parse_memory_type(stream: IO[bytes]) -> MemoryType:
    limits = parse_limits(stream)
    return MemoryType(limits.min, limits.max)


def parse_memory(stream: IO[bytes]) -> Memory:
    memory_type = parse_memory_type(stream)
    return Memory(memory_type)
