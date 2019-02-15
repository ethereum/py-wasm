from typing import (
    IO,
    Iterable,
    cast,
)

from wasm._utils.decorators import (
    to_tuple,
)
from wasm.instructions import (
    BaseInstruction,
)
from wasm.opcodes import (
    BinaryOpcode,
)

from .instructions import (
    parse_instruction,
)


@to_tuple
def parse_expression(stream: IO[bytes]) -> Iterable[BaseInstruction]:
    """
    Helper for parsing a sequence of instructions
    """
    while True:
        instruction = cast(BaseInstruction, parse_instruction(stream))

        yield instruction

        if instruction.opcode is BinaryOpcode.END:
            break
