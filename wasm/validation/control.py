from typing import (
    cast,
)

from wasm.datatypes import (
    TableIdx,
    ValType,
)
from wasm.exceptions import (
    ValidationError,
)
from wasm.instructions import (
    BaseInstruction,
    Block,
    Br,
    BrIf,
    BrTable,
    Call,
    CallIndirect,
    Else,
    If,
    Loop,
)
from wasm.opcodes import (
    BinaryOpcode,
)

from .context import (
    ExpressionContext,
)


def validate_control_instruction(instruction: BaseInstruction, ctx: ExpressionContext) -> None:
    if instruction.opcode is BinaryOpcode.UNREACHABLE:
        validate_unreachable(ctx)
    elif instruction.opcode is BinaryOpcode.BLOCK:
        validate_block(cast(Block, instruction), ctx)
    elif instruction.opcode is BinaryOpcode.END:
        validate_end(ctx)
    elif instruction.opcode is BinaryOpcode.IF:
        validate_if(cast(If, instruction), ctx)
    elif instruction.opcode is BinaryOpcode.ELSE:
        validate_else(cast(Else, instruction), ctx)
    elif instruction.opcode is BinaryOpcode.LOOP:
        validate_loop(cast(Loop, instruction), ctx)
    elif instruction.opcode is BinaryOpcode.BR:
        validate_br(cast(Br, instruction), ctx)
    elif instruction.opcode is BinaryOpcode.BR_IF:
        validate_br_if(cast(BrIf, instruction), ctx)
    elif instruction.opcode is BinaryOpcode.BR_TABLE:
        validate_br_table(cast(BrTable, instruction), ctx)
    elif instruction.opcode is BinaryOpcode.NOP:
        pass  # NOP is always valid
    elif instruction.opcode is BinaryOpcode.CALL:
        validate_call(cast(Call, instruction), ctx)
    elif instruction.opcode is BinaryOpcode.CALL_INDIRECT:
        validate_call_indirect(cast(CallIndirect, instruction), ctx)
    elif instruction.opcode is BinaryOpcode.RETURN:
        validate_return(ctx)
    else:
        raise Exception(f"Invariant: unhandled opcode {instruction.opcode}")


def validate_unreachable(ctx: ExpressionContext) -> None:
    ctx.mark_unreachable()


def validate_block(instruction: Block, ctx: ExpressionContext) -> None:
    ctx.push_control_frame(instruction.result_type, instruction.result_type)


def validate_if(instruction: If, ctx: ExpressionContext) -> None:
    ctx.pop_operand_and_assert_type(ValType.i32)
    ctx.push_control_frame(instruction.result_type, instruction.result_type)


def validate_else(instruction: Else, ctx: ExpressionContext) -> None:
    frame = ctx.pop_control_frame()
    ctx.push_control_frame(frame.end_types, frame.end_types)


def validate_br_if(instruction: BrIf, ctx: ExpressionContext) -> None:
    ctx.control_stack.validate_label_idx(instruction.label_idx)

    frame = ctx.control_stack.get_by_label_idx(instruction.label_idx)
    label_types = frame.label_types

    ctx.pop_operand_and_assert_type(ValType.i32)
    ctx.pop_operands_of_expected_types(label_types)

    for valtype in label_types:
        ctx.operand_stack.push(valtype)


def validate_end(ctx: ExpressionContext) -> None:
    frame = ctx.pop_control_frame()
    for valtype in frame.end_types:
        ctx.operand_stack.push(valtype)


def validate_loop(instruction: Loop, ctx: ExpressionContext) -> None:
    ctx.push_control_frame(tuple(), instruction.result_type)


def validate_br(instruction: Br, ctx: ExpressionContext) -> None:
    ctx.control_stack.validate_label_idx(instruction.label_idx)

    frame = ctx.control_stack.get_by_label_idx(instruction.label_idx)
    expected_label_types = frame.label_types

    ctx.pop_operands_of_expected_types(expected_label_types)
    ctx.mark_unreachable()


def validate_br_table(instruction: BrTable, ctx: ExpressionContext) -> None:
    ctx.control_stack.validate_label_idx(instruction.default_idx)

    frame = ctx.control_stack.get_by_label_idx(instruction.default_idx)
    expected_label_types = frame.label_types

    for idx, label_idx in enumerate(instruction.label_indices):
        ctx.control_stack.validate_label_idx(label_idx)
        label_frame = ctx.control_stack.get_by_label_idx(label_idx)

        if label_frame.label_types != expected_label_types:
            raise ValidationError(
                f"Label index at position {idx} has incorrect type.  Expected: "
                f"{expected_label_types}  Got: {label_frame.label_types}"
            )

    ctx.pop_operand_and_assert_type(ValType.i32)
    ctx.pop_operands_of_expected_types(expected_label_types)
    ctx.mark_unreachable()


def validate_call(instruction: Call, ctx: ExpressionContext) -> None:
    ctx.validate_function_idx(instruction.function_idx)
    function_type = ctx.get_function(instruction.function_idx)

    ctx.pop_operands_of_expected_types(function_type.params)
    for valtype in function_type.results:
        ctx.operand_stack.push(valtype)


def validate_call_indirect(instruction: CallIndirect, ctx: ExpressionContext) -> None:
    ctx.validate_table_idx(TableIdx(0))
    ctx.validate_type_idx(instruction.type_idx)
    function_type = ctx.get_type(instruction.type_idx)

    ctx.pop_operand_and_assert_type(ValType.i32)
    ctx.pop_operands_of_expected_types(function_type.params)

    for valtype in function_type.results:
        ctx.operand_stack.push(valtype)


def validate_return(ctx: ExpressionContext) -> None:
    if ctx.returns is not None:
        ctx.pop_operands_of_expected_types(ctx.returns)
    ctx.mark_unreachable()
