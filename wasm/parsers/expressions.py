from typing import (
    IO,
    Iterable,
    Tuple,
    cast,
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


def parse_expression(stream: IO[bytes]) -> Tuple[BaseInstruction, ...]:
    return tuple(_parse_expression(stream))


def _parse_expression(stream: IO[bytes]) -> Iterable[BaseInstruction]:
    while True:
        instruction = cast(BaseInstruction, parse_instruction(stream))

        yield instruction

        if instruction.opcode is BinaryOpcode.END:
            break
