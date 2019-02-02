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
    Context,
)


def validate_control_instruction(instruction: BaseInstruction, context: Context) -> None:
    if instruction.opcode is BinaryOpcode.UNREACHABLE:
        validate_unreachable(context)
    elif instruction.opcode is BinaryOpcode.BLOCK:
        validate_block(cast(Block, instruction), context)
    elif instruction.opcode is BinaryOpcode.END:
        validate_end(context)
    elif instruction.opcode is BinaryOpcode.IF:
        validate_if(cast(If, instruction), context)
    elif instruction.opcode is BinaryOpcode.ELSE:
        validate_else(cast(Else, instruction), context)
    elif instruction.opcode is BinaryOpcode.LOOP:
        validate_loop(cast(Loop, instruction), context)
    elif instruction.opcode is BinaryOpcode.BR:
        validate_br(cast(Br, instruction), context)
    elif instruction.opcode is BinaryOpcode.BR_IF:
        validate_br_if(cast(BrIf, instruction), context)
    elif instruction.opcode is BinaryOpcode.BR_TABLE:
        validate_br_table(cast(BrTable, instruction), context)
    elif instruction.opcode is BinaryOpcode.NOP:
        pass  # NOP is always valid
    elif instruction.opcode is BinaryOpcode.CALL:
        validate_call(cast(Call, instruction), context)
    elif instruction.opcode is BinaryOpcode.CALL_INDIRECT:
        validate_call_indirect(cast(CallIndirect, instruction), context)
    elif instruction.opcode is BinaryOpcode.RETURN:
        validate_return(context)
    else:
        raise Exception(f"Invariant: unhandled opcode {instruction.opcode}")


def validate_unreachable(context: Context) -> None:
    context.mark_unreachable()


def validate_block(instruction: Block, context: Context) -> None:
    context.push_control_frame(instruction.result_type, instruction.result_type)


def validate_if(instruction: If, context: Context) -> None:
    context.pop_operand_and_assert_type(ValType.i32)
    context.push_control_frame(instruction.result_type, instruction.result_type)


def validate_else(instruction: Else, context: Context) -> None:
    frame = context.pop_control_frame()
    context.push_control_frame(frame.end_types, frame.end_types)


def validate_br_if(instruction: BrIf, context: Context) -> None:
    context.control_stack.validate_label_idx(instruction.label_idx)

    frame = context.control_stack.get_by_label_idx(instruction.label_idx)
    label_types = frame.label_types

    context.pop_operand_and_assert_type(ValType.i32)
    context.pop_operands_of_expected_types(label_types)

    for valtype in label_types:
        context.operand_stack.push(valtype)


def validate_end(context: Context) -> None:
    frame = context.pop_control_frame()
    for valtype in frame.end_types:
        context.operand_stack.push(valtype)


def validate_loop(instruction: Loop, context: Context) -> None:
    context.push_control_frame(tuple(), instruction.result_type)


def validate_br(instruction: Br, context: Context) -> None:
    context.control_stack.validate_label_idx(instruction.label_idx)

    frame = context.control_stack.get_by_label_idx(instruction.label_idx)
    expected_label_types = frame.label_types

    context.pop_operands_of_expected_types(expected_label_types)
    context.mark_unreachable()


def validate_br_table(instruction: BrTable, context: Context) -> None:
    context.control_stack.validate_label_idx(instruction.default_idx)

    frame = context.control_stack.get_by_label_idx(instruction.default_idx)
    expected_label_types = frame.label_types

    for idx, label_idx in enumerate(instruction.label_indices):
        context.control_stack.validate_label_idx(label_idx)
        label_frame = context.control_stack.get_by_label_idx(label_idx)

        if label_frame.label_types != expected_label_types:
            raise ValidationError(
                f"Label index at position {idx} has incorrect type.  Expected: "
                f"{expected_label_types}  Got: {label_frame.label_types}"
            )

    context.pop_operand_and_assert_type(ValType.i32)
    context.pop_operands_of_expected_types(expected_label_types)
    context.mark_unreachable()


def validate_call(instruction: Call, context: Context) -> None:
    context.validate_function_idx(instruction.func_idx)
    function_type = context.get_function(instruction.func_idx)

    context.pop_operands_of_expected_types(function_type.params)
    for valtype in function_type.results:
        context.operand_stack.push(valtype)


def validate_call_indirect(instruction: CallIndirect, context: Context) -> None:
    context.validate_table_idx(TableIdx(0))
    context.validate_type_idx(instruction.type_idx)
    function_type = context.get_type(instruction.type_idx)

    context.pop_operand_and_assert_type(ValType.i32)
    context.pop_operands_of_expected_types(function_type.params)

    for valtype in function_type.results:
        context.operand_stack.push(valtype)


def validate_return(context: Context) -> None:
    if context.returns is not None:
        context.pop_operands_of_expected_types(context.returns)
    context.mark_unreachable()
