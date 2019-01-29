from wasm.opcodes import (
    BinaryOpcode,
)

from .base import (
    SimpleOp,
    register,
)


@register
class Drop(SimpleOp):
    opcode = BinaryOpcode.DROP


@register
class Select(SimpleOp):
    opcode = BinaryOpcode.SELECT
