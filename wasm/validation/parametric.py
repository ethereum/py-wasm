from wasm.datatypes import (
    ValType,
)
from wasm.instructions import (
    BaseInstruction,
)
from wasm.opcodes import (
    BinaryOpcode,
)

from .context import (
    ExpressionContext,
)


#
# Parametric Instructions
#
def validate_parametric_instruction(instruction: BaseInstruction, ctx: ExpressionContext) -> None:
    """
    Validate a single Parametric instruction as part of expression validation
    """
    if instruction.opcode is BinaryOpcode.DROP:
        validate_drop(ctx)
    elif instruction.opcode is BinaryOpcode.SELECT:
        validate_select(ctx)
    else:
        raise Exception(f"Invariant: unhandled opcode {instruction.opcode}")


def validate_drop(ctx: ExpressionContext) -> None:
    """
    Validate the Drop instruction as part of expression validation
    """
    ctx.pop_operand()


def validate_select(ctx: ExpressionContext) -> None:
    """
    Validate the Select instruction as part of expression validation
    """
    ctx.pop_operand_and_assert_type(ValType.i32)
    valtype = ctx.pop_operand()
    ctx.pop_operand_and_assert_type(valtype)
    ctx.operand_stack.push(valtype)
