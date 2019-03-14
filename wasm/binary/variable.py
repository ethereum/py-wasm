from typing import IO

from wasm.instructions import (
    GlobalOp,
    Instruction,
    LocalOp,
)
from wasm.opcodes import (
    BinaryOpcode,
)

from .indices import (
    parse_global_idx,
    parse_local_idx,
)


def parse_variable_instruction(opcode: BinaryOpcode,
                               stream: IO[bytes]) -> Instruction:
    """
    Parse a single Variable instruction
    """
    if opcode.is_local:
        local_idx = parse_local_idx(stream)
        return LocalOp.from_opcode(opcode, local_idx)
    elif opcode.is_global:
        global_idx = parse_global_idx(stream)
        return GlobalOp.from_opcode(opcode, global_idx)
    else:
        raise Exception(f"Invariant: got unknown opcode {opcode}")
