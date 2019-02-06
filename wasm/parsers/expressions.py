import io
from typing import (
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


def parse_expression(stream: io.BytesIO) -> Tuple[BaseInstruction, ...]:
    return tuple(_parse_expression(stream))


def _parse_expression(stream: io.BytesIO) -> Iterable[BaseInstruction]:
    while True:
        instruction = cast(BaseInstruction, parse_instruction(stream))

        yield instruction

        if instruction.opcode is BinaryOpcode.END:
            break
