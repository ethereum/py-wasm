from wasm.opcodes import (
    BinaryOpcode,
)

from .base import (
    SimpleOp,
    register,
)


@register
class Drop(SimpleOp):
    """
    Represenation of a DROP opcode
    """
    opcode = BinaryOpcode.DROP


@register
class Select(SimpleOp):
    """
    Represenation of a SELECT opcode
    """
    opcode = BinaryOpcode.SELECT
