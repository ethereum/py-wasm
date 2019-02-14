from typing import (
    cast,
)

from wasm.datatypes import (
    Mutability,
)
from wasm.exceptions import (
    ValidationError,
)
from wasm.instructions import (
    BaseInstruction,
    GlobalOp,
    LocalOp,
)
from wasm.opcodes import (
    BinaryOpcode,
)

from .context import (
    ExpressionContext,
)


#
# Variable Instructions
#
def validate_variable_instruction(instruction: BaseInstruction, ctx: ExpressionContext) -> None:
    """
    Validate a single Variable instruction as part of expression validation
    """
    if instruction.opcode is BinaryOpcode.GET_LOCAL:
        validate_get_local(cast(LocalOp, instruction), ctx)
    elif instruction.opcode is BinaryOpcode.SET_LOCAL:
        validate_set_local(cast(LocalOp, instruction), ctx)
    elif instruction.opcode is BinaryOpcode.TEE_LOCAL:
        validate_tee_local(cast(LocalOp, instruction), ctx)
    elif instruction.opcode is BinaryOpcode.GET_GLOBAL:
        validate_get_global(cast(GlobalOp, instruction), ctx)
    elif instruction.opcode is BinaryOpcode.SET_GLOBAL:
        validate_set_global(cast(GlobalOp, instruction), ctx)
    else:
        raise Exception(f"Invariant: unhandled opcode {instruction.opcode}")


def validate_get_local(instruction: LocalOp, ctx: ExpressionContext) -> None:
    """
    Validate the GET_LOCAL version of the LocalOp instruction as part of
    expression validation
    """
    ctx.validate_local_idx(instruction.local_idx)
    valtype = ctx.get_local(instruction.local_idx)
    ctx.operand_stack.push(valtype)


def validate_set_local(instruction: LocalOp, ctx: ExpressionContext) -> None:
    """
    Validate the SET_LOCAL version of the LocalOp instruction as part of
    expression validation
    """
    ctx.validate_local_idx(instruction.local_idx)
    valtype = ctx.get_local(instruction.local_idx)
    ctx.pop_operand_and_assert_type(valtype)


def validate_tee_local(instruction: LocalOp, ctx: ExpressionContext) -> None:
    """
    Validate the TEE_LOCAL version of the LocalOp instruction as part of
    expression validation
    """
    ctx.validate_local_idx(instruction.local_idx)
    valtype = ctx.get_local(instruction.local_idx)
    ctx.pop_operand_and_assert_type(valtype)
    ctx.operand_stack.push(valtype)


def validate_get_global(instruction: GlobalOp, ctx: ExpressionContext) -> None:
    """
    Validate the GET_GLOBAL version of the GlobalOp instruction as part of
    expression validation
    """
    ctx.validate_global_idx(instruction.global_idx)
    global_ = ctx.get_global(instruction.global_idx)
    ctx.operand_stack.push(global_.valtype)


def validate_set_global(instruction: GlobalOp, ctx: ExpressionContext) -> None:
    """
    Validate the SET_GLOBAL version of the GlobalOp instruction as part of
    expression validation
    """
    ctx.validate_global_idx(instruction.global_idx)
    global_ = ctx.get_global(instruction.global_idx)

    if global_.mut is not Mutability.var:  # type: ignore
        raise ValidationError(
            f"Global variable at index {instruction.global_idx} is immutable "
            "and cannot be modified"
        )

    ctx.pop_operand_and_assert_type(global_.valtype)
