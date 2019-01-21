import io

from wasm.instructions import (
    GlobalOp,
    Instruction,
    LocalOp,
)
from wasm.opcodes import (
    BinaryOpcode,
)

from .indices import (
    parse_globalidx,
    parse_localidx,
)


def parse_variable_instruction(opcode: BinaryOpcode,
                               stream: io.BytesIO) -> Instruction:
    if opcode.is_local:
        local_idx = parse_localidx(stream)
        return LocalOp.from_opcode(opcode, local_idx)
    elif opcode.is_global:
        global_idx = parse_globalidx(stream)
        return GlobalOp.from_opcode(opcode, global_idx)
    else:
        raise Exception(f"Invariant: got unknown opcode {opcode}")
