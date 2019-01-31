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
    Context,
)


#
# Variable Instructions
#
def validate_variable_instruction(instruction: BaseInstruction, context: Context) -> None:
    if instruction.opcode is BinaryOpcode.GET_LOCAL:
        validate_get_local(cast(LocalOp, instruction), context)
    elif instruction.opcode is BinaryOpcode.SET_LOCAL:
        validate_set_local(cast(LocalOp, instruction), context)
    elif instruction.opcode is BinaryOpcode.TEE_LOCAL:
        validate_tee_local(cast(LocalOp, instruction), context)
    elif instruction.opcode is BinaryOpcode.GET_GLOBAL:
        validate_get_global(cast(GlobalOp, instruction), context)
    elif instruction.opcode is BinaryOpcode.SET_GLOBAL:
        validate_set_global(cast(GlobalOp, instruction), context)
    else:
        raise Exception(f"Invariant: unhandled opcode {instruction.opcode}")


def validate_get_local(instruction: LocalOp, context: Context) -> None:
    context.validate_local_idx(instruction.local_idx)
    valtype = context.get_local(instruction.local_idx)
    context.operand_stack.push(valtype)


def validate_set_local(instruction: LocalOp, context: Context) -> None:
    context.validate_local_idx(instruction.local_idx)
    valtype = context.get_local(instruction.local_idx)
    context.pop_operand_and_assert_type(valtype)


def validate_tee_local(instruction: LocalOp, context: Context) -> None:
    context.validate_local_idx(instruction.local_idx)
    valtype = context.get_local(instruction.local_idx)
    context.pop_operand_and_assert_type(valtype)
    context.operand_stack.push(valtype)


def validate_get_global(instruction: GlobalOp, context: Context) -> None:
    context.validate_global_idx(instruction.global_idx)
    global_ = context.get_global(instruction.global_idx)
    context.operand_stack.push(global_.valtype)


def validate_set_global(instruction: GlobalOp, context: Context) -> None:
    context.validate_global_idx(instruction.global_idx)
    global_ = context.get_global(instruction.global_idx)

    if global_.mut is not Mutability.var:  # type: ignore
        raise ValidationError(
            f"Global variable at index {instruction.global_idx} is immutable "
            "and cannot be modified"
        )

    context.pop_operand_and_assert_type(global_.valtype)
