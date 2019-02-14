from typing import (
    cast,
)

from wasm import (
    constants,
)
from wasm.datatypes import (
    Limits,
    Memory,
    MemoryIdx,
    MemoryType,
    ValType,
)
from wasm.exceptions import (
    ValidationError,
)
from wasm.instructions import (
    BaseInstruction,
    MemoryOp,
)
from wasm.opcodes import (
    BinaryOpcode,
)

from .context import (
    ExpressionContext,
)
from .limits import (
    validate_limits,
)


def validate_memory_type(memory_type: MemoryType) -> None:
    """
    Validate a MemoryType object.
    """
    limits = Limits(memory_type.min, memory_type.max)
    validate_limits(limits, constants.UINT16_CEIL)


def validate_memory(memory: Memory) -> None:
    """
    Validate a Memory object.
    """
    validate_memory_type(memory.type)


def validate_memory_instruction(instruction: BaseInstruction, ctx: ExpressionContext) -> None:
    """
    Validate a single Memory instruction as part of expression validation
    """
    if instruction.opcode.is_memory_load:
        validate_memory_load(cast(MemoryOp, instruction), ctx)
    elif instruction.opcode.is_memory_store:
        validate_memory_store(cast(MemoryOp, instruction), ctx)
    elif instruction.opcode is BinaryOpcode.MEMORY_SIZE:
        validate_memory_size(ctx)
    elif instruction.opcode is BinaryOpcode.MEMORY_GROW:
        validate_memory_grow(ctx)
    else:
        raise Exception(f"Invariant: unhandled opcode {instruction.opcode}")


def validate_memory_load(instruction: MemoryOp, ctx: ExpressionContext) -> None:
    """
    Validate one of the LOAD memory instruction as part of expression validation
    """
    ctx.validate_mem_idx(MemoryIdx(0))

    align_ceil = instruction.memory_bit_size.value // 8
    if 2 ** instruction.memarg.align > align_ceil:
        raise ValidationError("Invalid memarg alignment")

    ctx.pop_operand_and_assert_type(ValType.i32)
    ctx.operand_stack.push(instruction.valtype)


def validate_memory_store(instruction: MemoryOp, ctx: ExpressionContext) -> None:
    """
    Validate one of the STORE memory instruction as part of expression validation
    """
    ctx.validate_mem_idx(MemoryIdx(0))

    align_ceil = instruction.memory_bit_size.value // 8
    if 2 ** instruction.memarg.align > align_ceil:
        raise ValidationError("Invalid memarg alignment")

    ctx.pop_operand_and_assert_type(instruction.valtype)
    ctx.pop_operand_and_assert_type(ValType.i32)


def validate_memory_size(ctx: ExpressionContext) -> None:
    """
    Validate the MEMORY_SIZE instruction as part of expression validation
    """
    ctx.validate_mem_idx(MemoryIdx(0))

    ctx.operand_stack.push(ValType.i32)


def validate_memory_grow(ctx: ExpressionContext) -> None:
    """
    Validate the MEMORY_GROW instruction as part of expression validation
    """
    ctx.validate_mem_idx(MemoryIdx(0))

    ctx.pop_operand_and_assert_type(ValType.i32)
    ctx.operand_stack.push(ValType.i32)
