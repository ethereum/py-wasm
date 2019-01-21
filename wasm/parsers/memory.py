import io

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
from .null import (
    parse_null_byte,
)


def parse_memory_instruction(opcode: BinaryOpcode,
                             stream: io.BytesIO) -> Instruction:
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


def parse_memarg(stream: io.BytesIO) -> MemoryArg:
    align = parse_u32(stream)
    offset = parse_u32(stream)
    return MemoryArg(offset, align)
