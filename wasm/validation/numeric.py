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
    ExpressionContext,
)

TNumericConstant = Union[I32Const, I64Const, F32Const, F64Const]
TConversion = Union[Wrap, Truncate, Convert, Reinterpret]


def validate_numeric_instruction(instruction: BaseInstruction, ctx: ExpressionContext) -> None:
    if instruction.opcode.is_numeric_constant:
        validate_numeric_constant(cast(TNumericConstant, instruction), ctx)
    elif instruction.opcode.is_relop:
        validate_relop(cast(RelOp, instruction), ctx)
    elif instruction.opcode.is_unop:
        validate_unop(cast(UnOp, instruction), ctx)
    elif instruction.opcode.is_binop:
        validate_binop(cast(BinOp, instruction), ctx)
    elif instruction.opcode.is_testop:
        validate_testop(cast(TestOp, instruction), ctx)
    elif instruction.opcode.is_conversion:
        validate_conversion(cast(TConversion, instruction), ctx)
    else:
        raise Exception(f"Invariant: unhandled opcode {instruction.opcode}")


def validate_numeric_constant(instruction: TNumericConstant, ctx: ExpressionContext) -> None:
    ctx.operand_stack.push(instruction.valtype)


def validate_relop(instruction: RelOp, ctx: ExpressionContext) -> None:
    ctx.pop_operand_and_assert_type(instruction.valtype)
    ctx.pop_operand_and_assert_type(instruction.valtype)
    ctx.operand_stack.push(ValType.i32)


def validate_unop(instruction: UnOp, ctx: ExpressionContext) -> None:
    ctx.pop_operand_and_assert_type(instruction.valtype)
    ctx.operand_stack.push(instruction.valtype)


def validate_binop(instruction: BinOp, ctx: ExpressionContext) -> None:
    ctx.pop_operand_and_assert_type(instruction.valtype)
    ctx.pop_operand_and_assert_type(instruction.valtype)
    ctx.operand_stack.push(instruction.valtype)


def validate_testop(instruction: TestOp, ctx: ExpressionContext) -> None:
    ctx.pop_operand_and_assert_type(instruction.valtype)
    ctx.operand_stack.push(ValType.i32)


def validate_conversion(instruction: TConversion, ctx: ExpressionContext) -> None:
    if instruction.opcode is BinaryOpcode.I32_WRAP_I64:
        validate_wrap(ctx)
    elif instruction.opcode in {BinaryOpcode.I64_EXTEND_S_I32, BinaryOpcode.I64_EXTEND_U_I32}:
        validate_extend(ctx)
    elif instruction.opcode.is_truncate:
        validate_truncate(cast(Truncate, instruction), ctx)
    elif instruction.opcode.is_convert:
        validate_convert(cast(Convert, instruction), ctx)
    elif instruction.opcode is BinaryOpcode.F64_PROMOTE_F32:
        validate_promote(ctx)
    elif instruction.opcode is BinaryOpcode.F32_DEMOTE_F64:
        validate_demote(ctx)
    elif instruction.opcode.is_reinterpret:
        validate_reinterpret(cast(Reinterpret, instruction), ctx)
    else:
        raise Exception(f"Invariant: unhandled opcode {instruction.opcode}")


def validate_wrap(ctx: ExpressionContext) -> None:
    ctx.pop_operand_and_assert_type(ValType.i64)
    ctx.operand_stack.push(ValType.i32)


def validate_extend(ctx: ExpressionContext) -> None:
    ctx.pop_operand_and_assert_type(ValType.i32)
    ctx.operand_stack.push(ValType.i64)


def validate_truncate(instruction: Truncate, ctx: ExpressionContext) -> None:
    ctx.pop_operand_and_assert_type(instruction.result)
    ctx.operand_stack.push(instruction.valtype)


def validate_convert(instruction: Convert, ctx: ExpressionContext) -> None:
    ctx.pop_operand_and_assert_type(instruction.result)
    ctx.operand_stack.push(instruction.valtype)


def validate_promote(ctx: ExpressionContext) -> None:
    ctx.pop_operand_and_assert_type(ValType.f32)
    ctx.operand_stack.push(ValType.f64)


def validate_demote(ctx: ExpressionContext) -> None:
    ctx.pop_operand_and_assert_type(ValType.f64)
    ctx.operand_stack.push(ValType.f32)


def validate_reinterpret(instruction: Reinterpret, ctx: ExpressionContext) -> None:
    ctx.pop_operand_and_assert_type(instruction.result)
    ctx.operand_stack.push(instruction.valtype)
