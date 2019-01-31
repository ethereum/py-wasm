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
)
from wasm.opcodes import (
    BinaryOpcode,
)

from .context import (
    Context,
)
from .control import (
    validate_control_instruction,
)
from .memory import (
    validate_memory_instruction,
)
from .numeric import (
    TNumericConstant,
    validate_numeric_constant,
    validate_numeric_instruction,
)
from .parametric import (
    validate_parametric_instruction,
)
from .variable import (
    validate_get_global,
    validate_variable_instruction,
)


def validate_instruction(instruction: BaseInstruction, context: Context) -> None:
    if instruction.opcode.is_control:
        validate_control_instruction(instruction, context)
    elif instruction.opcode.is_variable:
        validate_variable_instruction(instruction, context)
    elif instruction.opcode.is_memory:
        validate_memory_instruction(instruction, context)
    elif instruction.opcode.is_parametric:
        validate_parametric_instruction(instruction, context)
    elif instruction.opcode.is_numeric:
        validate_numeric_instruction(instruction, context)
    else:
        raise Exception(f"Invariant: unhandled opcode {instruction.opcode}")


def validate_constant_instruction(instruction: BaseInstruction, context: Context) -> None:
    if instruction.opcode is BinaryOpcode.GET_GLOBAL:
        global_ = context.get_global(cast(GlobalOp, instruction).global_idx)

        if global_.mut is not Mutability.const:
            raise ValidationError(
                "Attempt to access mutable global variable within constant "
                "expression"
            )
        validate_get_global(cast(GlobalOp, instruction), context)
    elif instruction.opcode.is_numeric_constant:
        validate_numeric_constant(cast(TNumericConstant, instruction), context)
    else:
        raise ValidationError(
            "Illegal instruction.  Only "
            "I32_CONST/I64_CONST/F32_CONST/F64_CONST/GET_GLOBAL are allowed. "
            f"Got {instruction.opcode}"
        )
