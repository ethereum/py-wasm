from typing import IO

from wasm.instructions import (
    BinOp,
    Convert,
    Demote,
    Extend,
    F32Const,
    F64Const,
    I32Const,
    I64Const,
    Instruction,
    Promote,
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

from .floats import (
    parse_f32,
    parse_f64,
)
from .integers import (
    parse_i32,
    parse_i64,
)


def parse_numeric_instruction(opcode: BinaryOpcode,
                              stream: IO[bytes]) -> Instruction:
    """
    Parse a single Numeric instruction.
    """
    if opcode.is_numeric_constant:
        return parse_numeric_constant_instruction(opcode, stream)
    elif opcode.is_relop:
        return RelOp.from_opcode(opcode)
    elif opcode.is_unop:
        return UnOp.from_opcode(opcode)
    elif opcode.is_binop:
        return BinOp.from_opcode(opcode)
    elif opcode.is_testop:
        return TestOp.from_opcode(opcode)
    elif opcode.is_conversion:
        return parse_conversion_instruction(opcode)
    else:
        raise Exception(f"Unhandled opcode: {opcode}")


def parse_numeric_constant_instruction(opcode: BinaryOpcode,
                                       stream: IO[bytes]) -> Instruction:
    """
    Parse a single CONST Numeric instruction.
    """
    if opcode is BinaryOpcode.I32_CONST:
        return I32Const.from_opcode(opcode, parse_i32(stream))
    elif opcode is BinaryOpcode.I64_CONST:
        return I64Const.from_opcode(opcode, parse_i64(stream))
    elif opcode is BinaryOpcode.F32_CONST:
        return F32Const.from_opcode(opcode, parse_f32(stream))
    elif opcode is BinaryOpcode.F64_CONST:
        return F64Const.from_opcode(opcode, parse_f64(stream))
    else:
        raise Exception("Invariant")


def parse_conversion_instruction(opcode: BinaryOpcode) -> Instruction:
    """
    Parse a single Wrap/Extend/Truncate/Convert/Promote/Demote/Reinterpret instruction
    """
    if opcode is BinaryOpcode.I32_WRAP_I64:
        return Wrap()
    elif opcode in {BinaryOpcode.I64_EXTEND_S_I32, BinaryOpcode.I64_EXTEND_U_I32}:
        return Extend.from_opcode(opcode)
    elif opcode.is_truncate:
        return Truncate.from_opcode(opcode)
    elif opcode.is_convert:
        return Convert.from_opcode(opcode)
    elif opcode is BinaryOpcode.F64_PROMOTE_F32:
        return Promote()
    elif opcode is BinaryOpcode.F32_DEMOTE_F64:
        return Demote()
    elif opcode.is_reinterpret:
        return Reinterpret.from_opcode(opcode)
    else:
        raise Exception(f"Invariant: unknown conversion opcode: {opcode}")
