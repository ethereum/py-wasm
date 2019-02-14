import logging
from typing import (
    Tuple,
    Union,
    cast,
)

from wasm.exceptions import (
    InvalidModule,
)
from wasm.instructions import (
    BaseInstruction,
    Block,
    If,
    Loop,
)
from wasm.opcodes import (
    BinaryOpcode,
)

from .context import (
    ExpressionContext,
)
from .instructions import (
    validate_constant_instruction,
    validate_instruction,
)

logger = logging.getLogger('wasm.validation.expression')


BLOCK_LOOP_IF = {
    BinaryOpcode.BLOCK,
    BinaryOpcode.LOOP,
    BinaryOpcode.IF,
}


def validate_expression(expression: Tuple[BaseInstruction, ...],
                        ctx: ExpressionContext) -> None:
    """
    Validate an expression
    """
    for idx, instruction in enumerate(expression):
        if not isinstance(instruction, BaseInstruction):
            # TODO: use a different exceptin since this represents an internal
            # failure.
            raise InvalidModule(
                f"Unrecognized instruction: {repr(instruction)} found at index "
                f"{idx}"
            )

        logger.debug('Validating instruction: %s', instruction)

        validate_instruction(instruction, ctx)

        # recurse for block, loop, if
        if instruction.opcode in BLOCK_LOOP_IF:
            sub_instructions = cast(Union[Block, Loop, If], instruction).instructions
            # RECURSION
            validate_expression(sub_instructions, ctx)

            if instruction.opcode is BinaryOpcode.IF:
                else_instructions = cast(If, instruction).else_instructions
                # RECURSION
                validate_expression(else_instructions, ctx)


def validate_constant_expression(expression: Tuple[BaseInstruction, ...],
                                 ctx: ExpressionContext) -> None:
    """
    Validate a constant expression
    """
    for idx, instruction in enumerate(expression[:-1]):
        if not isinstance(instruction, BaseInstruction):
            # TODO: use a different exceptin since this represents an internal
            # failure.
            raise InvalidModule(
                f"Unrecognized instruction: {repr(instruction)} found at index "
                f"{idx}"
            )
        logger.debug('Validating instruction: %s', instruction)

        validate_constant_instruction(instruction, ctx)
