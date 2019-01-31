from typing import (
    Union,
    cast,
)

from wasm.datatypes import (
    ValType,
)
from wasm.instructions import (
    BaseInstruction,
    BinOp,
    Convert,
    F32Const,
    F64Const,
    I32Const,
    I64Const,
    Reinterpret,
    RelOp,
    TestOp,
    Truncate,
    UnOp,
    Wrap,
)
from wasm.opcodes import (
    BinaryOpcode,
)

from .context import (
    Context,
)

TNumericConstant = Union[I32Const, I64Const, F32Const, F64Const]
TConversion = Union[Wrap, Truncate, Convert, Reinterpret]


def validate_numeric_instruction(instruction: BaseInstruction, context: Context) -> None:
    if instruction.opcode.is_numeric_constant:
        validate_numeric_constant(cast(TNumericConstant, instruction), context)
    elif instruction.opcode.is_relop:
        validate_relop(cast(RelOp, instruction), context)
    elif instruction.opcode.is_unop:
        validate_unop(cast(UnOp, instruction), context)
    elif instruction.opcode.is_binop:
        validate_binop(cast(BinOp, instruction), context)
    elif instruction.opcode.is_testop:
        validate_testop(cast(TestOp, instruction), context)
    elif instruction.opcode.is_conversion:
        validate_conversion(cast(TConversion, instruction), context)
    else:
        raise Exception(f"Invariant: unhandled opcode {instruction.opcode}")


def validate_numeric_constant(instruction: TNumericConstant, context: Context) -> None:
    context.operand_stack.push(instruction.valtype)


def validate_relop(instruction: RelOp, context: Context) -> None:
    context.pop_operand_and_assert_type(instruction.valtype)
    context.pop_operand_and_assert_type(instruction.valtype)
    context.operand_stack.push(ValType.i32)


def validate_unop(instruction: UnOp, context: Context) -> None:
    context.pop_operand_and_assert_type(instruction.valtype)
    context.operand_stack.push(instruction.valtype)


def validate_binop(instruction: BinOp, context: Context) -> None:
    context.pop_operand_and_assert_type(instruction.valtype)
    context.pop_operand_and_assert_type(instruction.valtype)
    context.operand_stack.push(instruction.valtype)


def validate_testop(instruction: TestOp, context: Context) -> None:
    context.pop_operand_and_assert_type(instruction.valtype)
    context.operand_stack.push(ValType.i32)


def validate_conversion(instruction: TConversion, context: Context) -> None:
    if instruction.opcode is BinaryOpcode.I32_WRAP_I64:
        validate_wrap(context)
    elif instruction.opcode in {BinaryOpcode.I64_EXTEND_S_I32, BinaryOpcode.I64_EXTEND_U_I32}:
        validate_extend(context)
    elif instruction.opcode.is_truncate:
        validate_truncate(cast(Truncate, instruction), context)
    elif instruction.opcode.is_convert:
        validate_convert(cast(Convert, instruction), context)
    elif instruction.opcode is BinaryOpcode.F64_PROMOTE_F32:
        validate_promote(context)
    elif instruction.opcode is BinaryOpcode.F32_DEMOTE_F64:
        validate_demote(context)
    elif instruction.opcode.is_reinterpret:
        validate_reinterpret(cast(Reinterpret, instruction), context)
    else:
        raise Exception(f"Invariant: unhandled opcode {instruction.opcode}")


def validate_wrap(context: Context) -> None:
    context.pop_operand_and_assert_type(ValType.i64)
    context.operand_stack.push(ValType.i32)


def validate_extend(context: Context) -> None:
    context.pop_operand_and_assert_type(ValType.i32)
    context.operand_stack.push(ValType.i64)


def validate_truncate(instruction: Truncate, context: Context) -> None:
    context.pop_operand_and_assert_type(instruction.result)
    context.operand_stack.push(instruction.valtype)


def validate_convert(instruction: Convert, context: Context) -> None:
    context.pop_operand_and_assert_type(instruction.result)
    context.operand_stack.push(instruction.valtype)


def validate_promote(context: Context) -> None:
    context.pop_operand_and_assert_type(ValType.f32)
    context.operand_stack.push(ValType.f64)


def validate_demote(context: Context) -> None:
    context.pop_operand_and_assert_type(ValType.f64)
    context.operand_stack.push(ValType.f32)


def validate_reinterpret(instruction: Reinterpret, context: Context) -> None:
    context.pop_operand_and_assert_type(instruction.result)
    context.operand_stack.push(instruction.valtype)
