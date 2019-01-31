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
    Context,
)
from .limits import (
    validate_limits,
)


def validate_memory_type(memory_type: MemoryType) -> None:
    limits = Limits(memory_type.min, memory_type.max)
    validate_limits(limits, constants.UINT16_CEIL)


def validate_memory(memory: Memory) -> None:
    validate_memory_type(memory.type)


def validate_memory_instruction(instruction: BaseInstruction, context: Context) -> None:
    if instruction.opcode.is_memory_load:
        validate_memory_load(cast(MemoryOp, instruction), context)
    elif instruction.opcode.is_memory_store:
        validate_memory_store(cast(MemoryOp, instruction), context)
    elif instruction.opcode is BinaryOpcode.MEMORY_SIZE:
        validate_memory_size(context)
    elif instruction.opcode is BinaryOpcode.MEMORY_GROW:
        validate_memory_grow(context)
    else:
        raise Exception(f"Invariant: unhandled opcode {instruction.opcode}")


def validate_memory_load(instruction: MemoryOp, context: Context) -> None:
    context.validate_mem_idx(MemoryIdx(0))

    align_ceil = instruction.memory_bit_size.value // 8
    if 2 ** instruction.memarg.align > align_ceil:
        raise ValidationError("Invalid memarg alignment")

    context.pop_operand_and_assert_type(ValType.i32)
    context.operand_stack.push(instruction.valtype)


def validate_memory_store(instruction: MemoryOp, context: Context) -> None:
    context.validate_mem_idx(MemoryIdx(0))

    align_ceil = instruction.memory_bit_size.value // 8
    if 2 ** instruction.memarg.align > align_ceil:
        raise ValidationError("Invalid memarg alignment")

    context.pop_operand_and_assert_type(instruction.valtype)
    context.pop_operand_and_assert_type(ValType.i32)


def validate_memory_size(context: Context) -> None:
    context.validate_mem_idx(MemoryIdx(0))

    context.operand_stack.push(ValType.i32)


def validate_memory_grow(context: Context) -> None:
    context.validate_mem_idx(MemoryIdx(0))

    context.pop_operand_and_assert_type(ValType.i32)
    context.operand_stack.push(ValType.i32)
