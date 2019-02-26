import logging
from typing import (
    TypeVar,
    Union,
    cast,
)

import numpy

from wasm import (
    constants,
)
from wasm._utils.numpy import (
    allow_invalid,
    allow_multiple,
    allow_overflow,
    allow_zerodiv,
)
from wasm.datatypes import (
    ValType,
)
from wasm.exceptions import (
    Trap,
)
from wasm.execution import (
    Configuration,
)
from wasm.instructions import (
    BinOp,
    Convert,
    Extend,
    F32Const,
    F64Const,
    I32Const,
    I64Const,
    RelOp,
    TestOp,
    Truncate,
    UnOp,
)
from wasm.typing import (
    Float,
)

logger = logging.getLogger('wasm.logic.numeric')

TConst = Union[F32Const, F64Const, I32Const, I64Const]


def const_op(config: Configuration) -> None:
    """
    Common logic function for the various CONST opcodes.
    """
    instruction = cast(TConst, config.instructions.current)
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", instruction.opcode.text, instruction)

    config.push_operand(instruction.value)


def ieqz_op(config: Configuration) -> None:
    """
    Common logic function for the integer EQZ opcodes
    """
    value = config.pop_operand()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", config.instructions.current.opcode.text, value)

    if value == 0:
        config.push_operand(constants.U32_ONE)
    else:
        config.push_operand(constants.U32_ZERO)


#
# Equality equality comparisons
#
def eq_op(config: Configuration) -> None:
    """
    Common logic function for all EQ opcodes
    """
    b, a = config.pop2_operands()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if a == b:
        config.push_operand(constants.U32_ONE)
    else:
        config.push_operand(constants.U32_ZERO)


def ne_op(config: Configuration) -> None:
    """
    Common logic function for all NE opcodes
    """
    b, a = config.pop2_operands()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if a == b:
        config.push_operand(constants.U32_ZERO)
    else:
        config.push_operand(constants.U32_ONE)


#
# Unsigned integer comparisons
#
def iltu_op(config: Configuration) -> None:
    """
    Common logic function for the integer LTU opcodes
    """
    b, a = config.pop2_operands()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if a < b:
        config.push_operand(constants.U32_ONE)
    else:
        config.push_operand(constants.U32_ZERO)


def ileu_op(config: Configuration) -> None:
    """
    Common logic function for the integer LEU opcodes
    """
    b, a = config.pop2_operands()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if a <= b:
        config.push_operand(constants.U32_ONE)
    else:
        config.push_operand(constants.U32_ZERO)


def igtu_op(config: Configuration) -> None:
    """
    Common logic function for the integer GTU opcodes
    """
    b, a = config.pop2_operands()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if a > b:
        config.push_operand(constants.U32_ONE)
    else:
        config.push_operand(constants.U32_ZERO)


def igeu_op(config: Configuration) -> None:
    """
    Common logic function for the integer GEU opcodes
    """
    b, a = config.pop2_operands()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if a >= b:
        config.push_operand(constants.U32_ONE)
    else:
        config.push_operand(constants.U32_ZERO)


#
# Signed integer comparisons
#
def iXX_lts_op(config: Configuration) -> None:
    """
    Common logic function for the integer LTS opcodes
    """
    instruction = cast(RelOp, config.instructions.current)
    b, a = config.pop2_u64()
    b_s = instruction.valtype.to_signed(b)
    a_s = instruction.valtype.to_signed(a)
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", instruction.opcode.text, a_s, b_s)

    if a_s < b_s:
        config.push_operand(constants.U32_ONE)
    else:
        config.push_operand(constants.U32_ZERO)


def iXX_les_op(config: Configuration) -> None:
    """
    Common logic function for the integer LES opcodes
    """
    instruction = cast(RelOp, config.instructions.current)
    b, a = config.pop2_u64()
    b_s = instruction.valtype.to_signed(b)
    a_s = instruction.valtype.to_signed(a)
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", instruction.opcode.text, a_s, b_s)

    if a_s <= b_s:
        config.push_operand(constants.U32_ONE)
    else:
        config.push_operand(constants.U32_ZERO)


def iXX_gts_op(config: Configuration) -> None:
    """
    Common logic function for the integer GTS opcodes
    """
    instruction = cast(RelOp, config.instructions.current)
    b, a = config.pop2_u64()
    b_s = instruction.valtype.to_signed(b)
    a_s = instruction.valtype.to_signed(a)
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", instruction.opcode.text, a_s, b_s)

    if a_s > b_s:
        config.push_operand(constants.U32_ONE)
    else:
        config.push_operand(constants.U32_ZERO)


def iXX_ges_op(config: Configuration) -> None:
    """
    Common logic function for the integer GES opcodes
    """
    instruction = cast(RelOp, config.instructions.current)
    b, a = config.pop2_u64()
    b_s = instruction.valtype.to_signed(b)
    a_s = instruction.valtype.to_signed(a)
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", instruction.opcode.text, a_s, b_s)

    if a_s >= b_s:
        config.push_operand(constants.U32_ONE)
    else:
        config.push_operand(constants.U32_ZERO)


#
# Integer addition
#
def iXX_add_op(config: Configuration) -> None:
    """
    Common logic function for the integer ADD opcodes
    """
    b, a = config.pop2_u64()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    with allow_overflow():
        config.push_operand(a + b)


def iXX_sub_op(config: Configuration) -> None:
    """
    Common logic function for the integer SUB opcodes
    """
    b, a = config.pop2_u64()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    with allow_overflow():
        config.push_operand(a - b)


#
# Integer multiplication
#
def iXX_mul_op(config: Configuration) -> None:
    """
    Common logic function for the integer MUL opcodes
    """
    b, a = config.pop2_u64()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    with allow_overflow():
        config.push_operand(a * b)


#
# Integer division
#
def idivu_op(config: Configuration) -> None:
    """
    Common logic function for the integer DIVU opcodes
    """
    b, a = config.pop2_u32()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if b == 0:
        raise Trap('DIVISION BY ZERO')
    config.push_operand(a // b)


def iXX_divs_op(config: Configuration) -> None:
    """
    Common logic function for the integer DIVS opcodes
    """
    instruction = cast(BinOp, config.instructions.current)
    b, a = config.pop2_u32()

    b_s = instruction.valtype.to_signed(b)
    a_s = instruction.valtype.to_signed(a)
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", instruction.opcode.text, a_s, b_s)

    if b == 0:
        raise Trap('DIVISION BY ZERO')

    raw_result = abs(int(a_s)) // abs(int(b_s))
    _, upper_bound = instruction.valtype.signed_bounds

    if raw_result > upper_bound:
        raise Trap('UNDEFINED')

    if (a_s < 0) is not (b_s < 0):
        signed_result = instruction.valtype.signed_type(-1 * raw_result)
    else:
        signed_result = instruction.valtype.signed_type(raw_result)

    result = instruction.valtype.from_signed(signed_result)

    config.push_operand(result)


#
# Count leading zeros
#
def iXX_clz_op(config: Configuration) -> None:
    """
    Common logic function for the integer CLZ opcodes
    """
    instruction = cast(TestOp, config.instructions.current)
    value = config.pop_u64()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", instruction.opcode.text, value)

    bit_size = instruction.valtype.bit_size.value
    if value == 0:
        config.push_operand(instruction.valtype.value(bit_size))
    else:
        config.push_operand(instruction.valtype.value(bit_size - int(value).bit_length()))


#
# Count trailing zeros
#
def iXX_ctz_op(config: Configuration) -> None:
    """
    Common logic function for the integer CTZ opcodes
    """
    instruction = cast(TestOp, config.instructions.current)
    value = config.pop_u64()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", instruction.opcode.text, value)

    if value == 0:
        config.push_operand(instruction.valtype.value(instruction.valtype.bit_size.value))
    else:
        as_bin = bin(int(value))
        _, _, zeros = as_bin.rpartition('1')
        config.push_operand(instruction.valtype.value(len(zeros)))


#
# Count non-zero bits
#
def ipopcnt_op(config: Configuration) -> None:
    """
    Common logic function for the integer POPCNT opcodes
    """
    instruction = cast(UnOp, config.instructions.current)
    value = config.pop_operand()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", instruction.opcode.text, value)

    if value == 0:
        config.push_operand(instruction.valtype.zero)
    else:
        config.push_operand(instruction.valtype.value(bin(int(value)).count('1')))


#
# Remainders
#
def iremu_op(config: Configuration) -> None:
    """
    Common logic function for the integer REMU opcodes
    """
    b, a = config.pop2_u64()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if b == 0:
        raise Trap('DIVISION BY ZERO')

    config.push_operand(a % b)


def iXX_rems_op(config: Configuration) -> None:
    """
    Common logic function for the integer REMS opcodes
    """
    instruction = cast(BinOp, config.instructions.current)
    b, a = config.pop2_u64()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", instruction.opcode.text, a, b)

    if b == 0:
        raise Trap('DIVISION BY ZERO')

    b_s = instruction.valtype.to_signed(b)
    a_s = instruction.valtype.to_signed(a)

    raw_result = numpy.abs(a_s) % numpy.abs(b_s)
    result = -1 * raw_result if a_s < 0 else raw_result

    config.push_operand(instruction.valtype.value(result))


#
# Logical and/or/xor
#
def iand_op(config: Configuration) -> None:
    """
    Common logic function for the integer AND opcodes
    """
    b, a = config.pop2_u64()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(a & b)


def ior_op(config: Configuration) -> None:
    """
    Common logic function for the integer OR opcodes
    """
    b, a = config.pop2_u64()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(a | b)


def ixor_op(config: Configuration) -> None:
    """
    Common logic function for the integer XOR opcodes
    """
    b, a = config.pop2_u64()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(a ^ b)


#
# Bitwise shifting
#
def iXX_shl_op(config: Configuration) -> None:
    """
    Common logic function for the integer SHL opcodes
    """
    instruction = cast(BinOp, config.instructions.current)
    b, a = config.pop2_u64()
    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", instruction.opcode.text, a, b)

    shift_amount = int(b % instruction.valtype.bit_size.value)
    raw_result = int(a) << shift_amount
    mod = instruction.valtype.mod
    config.push_operand(instruction.valtype.value(raw_result % mod))


def iXX_shr_sXX_op(config: Configuration) -> None:
    """
    Common logic function for the integer SHR opcodes
    """
    instruction = cast(BinOp, config.instructions.current)
    b, a_raw = config.pop2_u64()

    if instruction.signed:
        a = int(instruction.valtype.to_signed(a_raw))
    else:
        a = int(a_raw)

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", instruction.opcode.text, a, b)

    shift_amount = int(b % instruction.valtype.bit_size.value)

    if instruction.signed:
        result = instruction.valtype.from_signed(a >> shift_amount)
    else:
        result = instruction.valtype.value(a >> shift_amount)

    config.push_operand(result)


#
# Bitwise rotation
#
def iXX_rotl_op(config: Configuration) -> None:
    """
    Common logic function for the integer ROTL opcodes
    """
    instruction = cast(BinOp, config.instructions.current)
    b, a = config.pop2_u64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", instruction.opcode.text, a, b)

    bit_size = instruction.valtype.bit_size.value
    shift_size = int(b % bit_size)
    upper = int(a) << shift_size
    lower = int(a) >> int(bit_size - shift_size)
    result = (upper | lower) % instruction.valtype.mod

    config.push_operand(instruction.valtype.value(result))


def iXX_rotr_op(config: Configuration) -> None:
    """
    Common logic function for the integer ROTR opcodes
    """
    instruction = cast(BinOp, config.instructions.current)
    b, a = config.pop2_u64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", instruction.opcode.text, a, b)

    bit_size = instruction.valtype.bit_size.value
    shift_size = int(b % bit_size)
    lower = int(a) >> shift_size
    upper = int(a) << int(bit_size - shift_size)
    result = (upper | lower) % instruction.valtype.mod

    config.push_operand(instruction.valtype.value(result))


#
# Float comparisons
#
def flt_op(config: Configuration) -> None:
    """
    Common logic function for the float LT opcodes
    """
    b, a = config.pop2_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if numpy.isnan(a) or numpy.isnan(b):
        config.push_operand(constants.U32_ZERO)
    elif a.tobytes() == b.tobytes():
        config.push_operand(constants.U32_ZERO)
    elif numpy.isposinf(a):
        config.push_operand(constants.U32_ZERO)
    elif numpy.isneginf(a):
        config.push_operand(constants.U32_ONE)
    elif numpy.isposinf(b):
        config.push_operand(constants.U32_ONE)
    elif numpy.isneginf(b):
        config.push_operand(constants.U32_ZERO)
    elif a < b:
        config.push_operand(constants.U32_ONE)
    else:
        config.push_operand(constants.U32_ZERO)


def fgt_op(config: Configuration) -> None:
    """
    Common logic function for the float GT opcodes
    """
    b, a = config.pop2_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if numpy.isnan(a) or numpy.isnan(b):
        config.push_operand(constants.U32_ZERO)
    elif a.tobytes() == b.tobytes():
        config.push_operand(constants.U32_ZERO)
    elif numpy.isposinf(a):
        config.push_operand(constants.U32_ONE)
    elif numpy.isneginf(a):
        config.push_operand(constants.U32_ZERO)
    elif numpy.isposinf(b):
        config.push_operand(constants.U32_ZERO)
    elif numpy.isneginf(b):
        config.push_operand(constants.U32_ONE)
    elif a > b:
        config.push_operand(constants.U32_ONE)
    else:
        config.push_operand(constants.U32_ZERO)


def fle_op(config: Configuration) -> None:
    """
    Common logic function for the float LE opcodes
    """
    b, a = config.pop2_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if numpy.isnan(a) or numpy.isnan(b):
        config.push_operand(constants.U32_ZERO)
    elif a.tobytes() == b.tobytes():
        config.push_operand(constants.U32_ONE)
    elif numpy.isposinf(a):
        config.push_operand(constants.U32_ZERO)
    elif numpy.isneginf(a):
        config.push_operand(constants.U32_ONE)
    elif numpy.isposinf(b):
        config.push_operand(constants.U32_ONE)
    elif numpy.isneginf(b):
        config.push_operand(constants.U32_ZERO)
    elif a == 0 and b == 0:
        config.push_operand(constants.U32_ONE)
    elif a <= b:
        config.push_operand(constants.U32_ONE)
    else:
        config.push_operand(constants.U32_ZERO)


def fge_op(config: Configuration) -> None:
    """
    Common logic function for the float GT opcodes
    """
    b, a = config.pop2_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if numpy.isnan(a) or numpy.isnan(b):
        config.push_operand(constants.U32_ZERO)
    elif a.tobytes() == b.tobytes():
        config.push_operand(constants.U32_ONE)
    elif numpy.isposinf(a):
        config.push_operand(constants.U32_ONE)
    elif numpy.isneginf(a):
        config.push_operand(constants.U32_ZERO)
    elif numpy.isposinf(b):
        config.push_operand(constants.U32_ZERO)
    elif numpy.isneginf(b):
        config.push_operand(constants.U32_ONE)
    elif a == 0 and b == 0:
        config.push_operand(constants.U32_ONE)
    elif a >= b:
        config.push_operand(constants.U32_ONE)
    else:
        config.push_operand(constants.U32_ZERO)


#
# ABS and Neg
#
def fabs_op(config: Configuration) -> None:
    """
    Common logic function for the float ABS opcodes
    """
    instruction = cast(UnOp, config.instructions.current)

    a = config.pop_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", instruction.opcode.text, a)

    if numpy.isnan(a):
        if _is_negative(a):
            with allow_invalid():
                config.push_operand(_negate_float(a))
        else:
            config.push_operand(a)
    elif numpy.isinf(a):
        config.push_operand(instruction.valtype.inf)
    else:
        config.push_operand(numpy.abs(a))


FLOAT_SIGN_MASK = 0b10000000


def _is_negative(value: Float) -> bool:
    """
    Helper function which returns a boolean indicating if the floating point
    value is considered negative as determined by checking the value of the
    most significant bit.
    """
    return bool(value.tobytes()[-1] & FLOAT_SIGN_MASK)


TFloat = TypeVar('TFloat', bound=Float)


def _negate_float(value: TFloat) -> TFloat:
    """
    Helper function which returns the given floating point value with a negated
    sign by setting the most significant bit.
    """
    encoded_value = bytearray(value.data)

    is_negative = _is_negative(value)

    if is_negative:
        encoded_value[-1] &= 0b01111111
    else:
        encoded_value[-1] |= FLOAT_SIGN_MASK

    return numpy.frombuffer(encoded_value, type(value))[0]


def fneg_op(config: Configuration) -> None:
    """
    Common logic function for the float NEG opcodes
    """
    instruction = cast(UnOp, config.instructions.current)

    value = config.pop_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", instruction.opcode.text, value)

    negated_value = _negate_float(value)

    config.push_operand(negated_value)


def fceil_op(config: Configuration) -> None:
    """
    Common logic function for the float CEIL opcodes
    """
    instruction = cast(UnOp, config.instructions.current)

    value = config.pop_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", instruction.opcode.text, value)

    if numpy.isnan(value):
        with allow_invalid():
            config.push_operand(numpy.ceil(value))
    elif numpy.isinf(value):
        config.push_operand(value)
    elif value == 0:
        config.push_operand(value)
    elif -1.0 < value < 0.0:
        config.push_operand(instruction.valtype.negzero)
    else:
        config.push_operand(numpy.ceil(value))


def ffloor_op(config: Configuration) -> None:
    """
    Common logic function for the float FLOOR opcodes
    """
    value = config.pop_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", config.instructions.current.opcode.text, value)

    if numpy.isnan(value):
        with allow_invalid():
            config.push_operand(numpy.floor(value))
    elif numpy.isinf(value):
        config.push_operand(value)
    elif value == 0:
        config.push_operand(value)
    else:
        config.push_operand(numpy.floor(value))


def ftrunc_op(config: Configuration) -> None:
    """
    Common logic function for the float TRUNC opcodes
    """
    instruction = cast(UnOp, config.instructions.current)

    value = config.pop_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", instruction.opcode.text, value)

    if numpy.isnan(value):
        with allow_invalid():
            config.push_operand(numpy.trunc(value))
    elif numpy.isinf(value):
        config.push_operand(value)
    elif value == 0:
        config.push_operand(value)
    elif -1.0 < value < 0.0:
        # TODO: `numpy.trunc` properly handles this case, can be removed.
        config.push_operand(instruction.valtype.negzero)
    else:
        config.push_operand(numpy.trunc(value))


def fnearest_op(config: Configuration) -> None:
    """
    Common logic function for the float NEAREST opcodes
    """
    instruction = cast(UnOp, config.instructions.current)

    value = config.pop_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", instruction.opcode.text, value)

    if numpy.isnan(value):
        with allow_invalid():
            config.push_operand(numpy.round(value))
    elif numpy.isinf(value):
        config.push_operand(value)
    elif value == 0:
        config.push_operand(value)
    elif -0.5 <= value < 0.0:
        config.push_operand(instruction.valtype.negzero)
    else:
        config.push_operand(numpy.round(value))


def fsqrt_op(config: Configuration) -> None:
    """
    Common logic function for the float SQRT opcodes
    """
    instruction = cast(UnOp, config.instructions.current)

    value = config.pop_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", instruction.opcode.text, value)

    if numpy.isnan(value):
        with allow_invalid():
            config.push_operand(numpy.sqrt(value))
    elif value == 0:
        # TODO: this block and the subsequent _is_negative block are in
        # inverted order in the spec, indicating that the proper response here
        # should potentially be `nan` for the case of `sqrt(-0.0)` but the spec
        # tests assert that is not correct.
        # f32.wasm: line 2419
        config.push_operand(value)
    elif _is_negative(value):
        config.push_operand(instruction.valtype.nan)
    else:
        config.push_operand(numpy.sqrt(value))


#
# Helpers for floating point ops
#
def _same_signed(left: TFloat, right: TFloat) -> bool:
    """
    Helper function which return a boolean indicating whether both values have
    the same sign as measured by the value of their most significant bit.
    """
    left_is_negative = _is_negative(left)
    right_is_negative = _is_negative(right)
    return left_is_negative is right_is_negative


def _same_signed_inf(left: TFloat, right: TFloat) -> bool:
    """
    Helper function which return a boolean indicating whether both values are
    infinities with the same sign as measured by their most significant bit

    """
    if not numpy.isinf(left) or not numpy.isinf(right):
        return False
    return numpy.isposinf(left) is numpy.isposinf(right)


def _different_signed_inf(left: TFloat, right: TFloat) -> bool:
    """
    Helper function which return a boolean indicating whether both values are
    infinities but with different signs
    """
    if not numpy.isinf(left) or not numpy.isinf(right):
        return False
    return numpy.isposinf(left) is not numpy.isposinf(right)


#
# Float arithmetic
#
def fadd_op(config: Configuration) -> None:
    """
    Common logic function for the float ADD opcodes
    """
    b, a = config.pop2_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    with allow_multiple(over=True, invalid=True):
        config.push_operand(a + b)


def fsub_op(config: Configuration) -> None:
    """
    Common logic function for the float SUB opcodes
    """
    instruction = cast(BinOp, config.instructions.current)

    b, a = config.pop2_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", instruction.opcode.text, a, b)

    with allow_multiple(over=True, invalid=True):
        if numpy.isnan(a) or numpy.isnan(b):
            config.push_operand(a - b)
        elif _same_signed_inf(a, b):
            config.push_operand(a - b)
        elif numpy.isinf(a):
            config.push_operand(a)
        elif numpy.isinf(b):
            config.push_operand(instruction.valtype.value(-1) * b)
        else:
            config.push_operand(a - b)


def fmul_op(config: Configuration) -> None:
    """
    Common logic function for the float MUL opcodes
    """
    instruction = cast(BinOp, config.instructions.current)

    b, a = config.pop2_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", instruction.opcode.text, a, b)

    with allow_multiple(over=True, under=True, invalid=True):
        if numpy.isnan(a) or numpy.isnan(b):
            config.push_operand(a * b)
        elif _same_signed_inf(a, b):
            config.push_operand(instruction.valtype.inf)
        elif _different_signed_inf(a, b):
            config.push_operand(instruction.valtype.neginf)
        elif instruction.valtype is ValType.f64:
            config.push_operand(a * b)
        elif instruction.valtype is ValType.f32:
            config.push_operand(a * b)
        else:
            raise Exception("Unreachable")


def fdiv_op(config: Configuration) -> None:
    """
    Common logic function for the float DIV opcodes
    """
    instruction = cast(BinOp, config.instructions.current)

    b, a = config.pop2_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", instruction.opcode.text, a, b)

    with allow_multiple(over=True, under=True, invalid=True):
        if numpy.isnan(a) or numpy.isnan(b):
            config.push_operand(a / b)
        elif numpy.isinf(a) and numpy.isinf(b):
            config.push_operand(a / b)
        elif a == 0 and b == 0:
            with allow_zerodiv():
                config.push_operand(a / b)
        elif numpy.isinf(a):
            if _same_signed(a, b):
                config.push_operand(instruction.valtype.inf)
            else:
                config.push_operand(instruction.valtype.neginf)
        elif numpy.isinf(b):
            if _same_signed(a, b):
                config.push_operand(instruction.valtype.zero)
            else:
                config.push_operand(instruction.valtype.negzero)
        elif a == 0:
            if _same_signed(a, b):
                config.push_operand(instruction.valtype.zero)
            else:
                config.push_operand(instruction.valtype.negzero)
        elif b == 0:
            if _same_signed(a, b):
                config.push_operand(instruction.valtype.inf)
            else:
                config.push_operand(instruction.valtype.neginf)
        else:
            config.push_operand(a / b)


def fmin_op(config: Configuration) -> None:
    """
    Common logic function for the float MIN opcodes
    """
    instruction = cast(BinOp, config.instructions.current)

    b, a = config.pop2_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", instruction.opcode.text, a, b)

    if numpy.isnan(a) or numpy.isnan(b):
        with allow_invalid():
            config.push_operand(a + b)
    elif numpy.isneginf(a) or numpy.isneginf(b):
        config.push_operand(instruction.valtype.neginf)
    elif a == 0 and b == 0:
        if _same_signed(a, b):
            config.push_operand(a)
        else:
            config.push_operand(instruction.valtype.negzero)
    else:
        config.push_operand(min(a, b))


def fmax_op(config: Configuration) -> None:
    """
    Common logic function for the float MAX opcodes
    """
    instruction = cast(BinOp, config.instructions.current)

    b, a = config.pop2_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", instruction.opcode.text, a, b)

    if numpy.isnan(a) or numpy.isnan(b):
        with allow_invalid():
            config.push_operand(a + b)
    elif numpy.isposinf(a) or numpy.isposinf(b):
        config.push_operand(instruction.valtype.inf)
    elif a == 0 and b == 0:
        if _same_signed(a, b):
            config.push_operand(a)
        else:
            config.push_operand(instruction.valtype.zero)
    else:
        config.push_operand(max(a, b))


#
# Binary Operations
#
def fcopysign_op(config: Configuration) -> None:
    """
    Common logic function for the float COPYSIGN opcodes
    """
    b, a = config.pop2_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    a_is_negative = _is_negative(a)
    b_is_negative = _is_negative(b)

    if a_is_negative is b_is_negative:
        config.push_operand(a)
    else:
        config.push_operand(_negate_float(a))


#
# Wrap
#
def iwrap64_op(config: Configuration) -> None:
    """
    Logic function for the I32_WRAP_I64 opcode
    """
    value = config.pop_u64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", config.instructions.current.opcode.text, value)

    config.push_operand(numpy.uint32(value))


def iXX_trunc_usX_fXX_op(config: Configuration) -> None:
    """
    Common logic function for the TRUNC opcodes which convert a float to an
    integer
    """
    instruction = cast(Truncate, config.instructions.current)

    value = config.pop_f32()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", instruction.opcode.text, value)

    if numpy.isnan(value) or numpy.isinf(value):
        raise Trap(f"Truncation is undefined for {value}")
    else:
        trunc_value = int(numpy.trunc(value))

        if instruction.signed:
            s_lower_bound, s_upper_bound = instruction.valtype.signed_bounds
            if trunc_value < s_lower_bound or trunc_value > s_upper_bound:
                raise Trap(
                    f"Truncation is undefined for {value}. Result outside of s32 "
                    "range."
                )

            result = instruction.valtype.from_signed(instruction.valtype.signed_type(
                trunc_value
            ))
        else:
            u_lower_bound, u_upper_bound = instruction.valtype.bounds
            if trunc_value < u_lower_bound or trunc_value > u_upper_bound:
                raise Trap(
                    f"Truncation is undefined for {value}. Result outside of s32 "
                    "range."
                )
            result = instruction.valtype.value(trunc_value)

        config.push_operand(result)


def i64extend_usX_op(config: Configuration) -> None:
    """
    Common logic function for the EXTEND opcodes
    """
    instruction = cast(Extend, config.instructions.current)

    value = config.pop_u32()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", instruction.opcode.text, value)

    if instruction.signed:
        signed_value = instruction.from_valtype.to_signed(value)
        result = instruction.valtype.from_signed(signed_value)
    else:
        result = instruction.valtype.value(value)

    config.push_operand(result)


def fXX_convert_usX_iXX_op(config: Configuration) -> None:
    """
    Common logic function for the CONVERT opcodes
    """
    instruction = cast(Convert, config.instructions.current)

    base_value = config.pop_u64()

    if instruction.signed:
        value = instruction.from_valtype.to_signed(base_value)
    else:
        value = base_value

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", instruction.opcode.text, value)

    config.push_operand(instruction.valtype.to_float(value))


def f32demote_op(config: Configuration) -> None:
    """
    Logic function for the F32_DEMOTE_F64 opcode
    """
    value = config.pop_f64()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", config.instructions.current.opcode.text, value)

    config.push_operand(numpy.float32(value))


def f64promote_op(config: Configuration) -> None:
    """
    Logic function for the F64_PROMOTE_F32 opcode
    """
    value = config.pop_f32()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", config.instructions.current.opcode.text, value)

    if numpy.isnan(value):
        if _is_negative(value):
            config.push_operand(numpy.float64('-nan'))
        else:
            config.push_operand(numpy.float64('nan'))
    else:
        config.push_operand(numpy.float64(value))


def XXX_reinterpret_XXX_op(config: Configuration) -> None:
    """
    Common logic function for the REINTERPRET opcodes
    """
    instruction = cast(Convert, config.instructions.current)

    value = config.pop_f32()

    if config.enable_logic_fn_logging:
        logger.debug("%s(%s)", instruction.opcode.text, value)

    config.push_operand(numpy.frombuffer(value.data, instruction.valtype.value)[0])
