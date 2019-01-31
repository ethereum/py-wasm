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
    Context,
)


#
# Parametric Instructions
#
def validate_parametric_instruction(instruction: BaseInstruction, context: Context) -> None:
    if instruction.opcode is BinaryOpcode.DROP:
        validate_drop(context)
    elif instruction.opcode is BinaryOpcode.SELECT:
        validate_select(context)
    else:
        raise Exception(f"Invariant: unhandled opcode {instruction.opcode}")


def validate_drop(context: Context) -> None:
    context.pop_operand()


def validate_select(context: Context) -> None:
    context.pop_operand_and_assert_type(ValType.i32)
    valtype = context.pop_operand()
    context.pop_operand_and_assert_type(valtype)
    context.operand_stack.push(valtype)
