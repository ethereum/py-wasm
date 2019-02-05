import decimal
import logging
from typing import (
    Union,
    cast,
)

from wasm import (
    constants,
)
from wasm._utils.numeric import (
    s32_to_u32,
    s64_to_u64,
    u32_to_s32,
    u64_to_s64,
)
from wasm.exceptions import (
    Trap,
)
from wasm.execution import (
    Configuration,
)
from wasm.instructions import (
    F32Const,
    F64Const,
    I32Const,
    I64Const,
)
from wasm.typing import (
    SInt32,
    SInt64,
    UInt32,
    UInt64,
)

logger = logging.getLogger('wasm.logic.numeric')

TConst = Union[F32Const, F64Const, I32Const, I64Const]


def const_op(config: Configuration) -> None:
    instruction = cast(TConst, config.instructions.current)
    logger.debug("%s(%s)", instruction.opcode.text, instruction)

    config.push_operand(instruction.value)


def ieqz_op(config: Configuration) -> None:
    value = config.pop_operand()
    logger.debug("%s(%s)", config.instructions.current.opcode.text, value)

    if value == 0:
        config.push_operand(UInt32(1))
    else:
        config.push_operand(UInt32(0))


#
# Integer equality comparisons
#
def ieq_op(config: Configuration) -> None:
    b, a = config.pop2_operands()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if a == b:
        config.push_operand(UInt32(1))
    else:
        config.push_operand(UInt32(0))


def ine_op(config: Configuration) -> None:
    b, a = config.pop2_operands()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if a == b:
        config.push_operand(UInt32(0))
    else:
        config.push_operand(UInt32(1))


#
# Unsigned integer comparisons
#
def iltu_op(config: Configuration) -> None:
    b, a = config.pop2_operands()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if a < b:
        config.push_operand(UInt32(1))
    else:
        config.push_operand(UInt32(0))


def ileu_op(config: Configuration) -> None:
    b, a = config.pop2_operands()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if a <= b:
        config.push_operand(UInt32(1))
    else:
        config.push_operand(UInt32(0))


def igtu_op(config: Configuration) -> None:
    b, a = config.pop2_operands()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if a > b:
        config.push_operand(UInt32(1))
    else:
        config.push_operand(UInt32(0))


def igeu_op(config: Configuration) -> None:
    b, a = config.pop2_operands()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if a >= b:
        config.push_operand(UInt32(1))
    else:
        config.push_operand(UInt32(0))


#
# 32-bit Signed integer comparisons
#
def i32lts_op(config: Configuration) -> None:
    b, a = config.pop2_u32()
    b_s = u32_to_s32(b)
    a_s = u32_to_s32(a)
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a_s, b_s)

    if a_s < b_s:
        config.push_operand(UInt32(1))
    else:
        config.push_operand(UInt32(0))


def i32les_op(config: Configuration) -> None:
    b, a = config.pop2_u32()
    b_s = u32_to_s32(b)
    a_s = u32_to_s32(a)
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a_s, b_s)

    if a_s <= b_s:
        config.push_operand(UInt32(1))
    else:
        config.push_operand(UInt32(0))


def i32gts_op(config: Configuration) -> None:
    b, a = config.pop2_u32()
    b_s = u32_to_s32(b)
    a_s = u32_to_s32(a)
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a_s, b_s)

    if a_s > b_s:
        config.push_operand(UInt32(1))
    else:
        config.push_operand(UInt32(0))


def i32ges_op(config: Configuration) -> None:
    b, a = config.pop2_u32()
    b_s = u32_to_s32(b)
    a_s = u32_to_s32(a)
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a_s, b_s)

    if a_s >= b_s:
        config.push_operand(UInt32(1))
    else:
        config.push_operand(UInt32(0))


#
# 64-bit Signed integer comparisons
#
def i64lts_op(config: Configuration) -> None:
    b, a = config.pop2_u64()
    b_s = u64_to_s64(b)
    a_s = u64_to_s64(a)
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a_s, b_s)

    if a_s < b_s:
        config.push_operand(UInt32(1))
    else:
        config.push_operand(UInt32(0))


def i64les_op(config: Configuration) -> None:
    b, a = config.pop2_u64()
    b_s = u64_to_s64(b)
    a_s = u64_to_s64(a)
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a_s, b_s)

    if a_s <= b_s:
        config.push_operand(UInt32(1))
    else:
        config.push_operand(UInt32(0))


def i64gts_op(config: Configuration) -> None:
    b, a = config.pop2_u64()
    b_s = u64_to_s64(b)
    a_s = u64_to_s64(a)
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a_s, b_s)

    if a_s > b_s:
        config.push_operand(UInt32(1))
    else:
        config.push_operand(UInt32(0))


def i64ges_op(config: Configuration) -> None:
    b, a = config.pop2_u64()
    b_s = u64_to_s64(b)
    a_s = u64_to_s64(a)
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a_s, b_s)

    if a_s >= b_s:
        config.push_operand(UInt32(1))
    else:
        config.push_operand(UInt32(0))


#
# Integer addition
#
def i32add_op(config: Configuration) -> None:
    b, a = config.pop2_u32()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(UInt32((a + b) % constants.UINT32_CEIL))


def i64add_op(config: Configuration) -> None:
    b, a = config.pop2_u64()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(UInt64((a + b) % constants.UINT64_CEIL))


def i32sub_op(config: Configuration) -> None:
    b, a = config.pop2_u32()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(UInt32((a - b) % constants.UINT32_CEIL))


def i64sub_op(config: Configuration) -> None:
    b, a = config.pop2_u64()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(UInt64((a - b) % constants.UINT64_CEIL))


#
# Integer multiplication
#
def i32mul_op(config: Configuration) -> None:
    b, a = config.pop2_u32()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(UInt32((a * b) % constants.UINT32_CEIL))


def i64mul_op(config: Configuration) -> None:
    b, a = config.pop2_u64()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(UInt64((a * b) % constants.UINT64_CEIL))


#
# Integer division
#
def idivu_op(config: Configuration) -> None:
    b, a = config.pop2_u32()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if b == 0:
        raise Trap('DIVISION BY ZERO')
    config.push_operand(UInt32(a // b))


def i32divs_op(config: Configuration) -> None:
    b, a = config.pop2_u32()

    b_s = u32_to_s32(b)
    a_s = u32_to_s32(a)
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a_s, b_s)

    if b == 0:
        raise Trap('DIVISION BY ZERO')

    raw_result = a_s / b_s
    if raw_result == constants.SINT32_CEIL:
        raise Trap('UNDEFINED')
    config.push_operand(s32_to_u32(SInt32(int(raw_result))))


def i64divs_op(config: Configuration) -> None:
    b, a = config.pop2_u64()

    b_s = u64_to_s64(b)
    a_s = u64_to_s64(a)
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a_s, b_s)

    if b == 0:
        raise Trap('DIVISION BY ZERO')

    # decimal wrapping needed to ensure float precision doesn't cause rounding
    # error.  21 *appears* to be the right precision, since 2**64 has 20 digits
    # and we want one more to handle correct rounding.
    with decimal.localcontext() as ctx:
        ctx.prec = 21
        raw_result = decimal.Decimal(a_s) / b_s
    if raw_result == constants.SINT64_CEIL:
        raise Trap('UNDEFINED')
    config.push_operand(s64_to_u64(SInt64(int(raw_result))))


#
# Count leading zeros
#
def i32clz_op(config: Configuration) -> None:
    value = config.pop_u32()
    logger.debug("%s(%s)", config.instructions.current.opcode.text, value)

    config.push_operand(UInt32(32 - value.bit_length()))


def i64clz_op(config: Configuration) -> None:
    value = config.pop_u64()
    logger.debug("%s(%s)", config.instructions.current.opcode.text, value)

    config.push_operand(UInt64(64 - value.bit_length()))


POWERS_OF_TWO = tuple(
    2**i
    for i in range(64)
)


#
# Count trailing zeros
#
def i32ctz_op(config: Configuration) -> None:
    value = config.pop_u32()
    logger.debug("%s(%s)", config.instructions.current.opcode.text, value)

    if value == 0:
        config.push_operand(UInt32(32))
    else:
        for idx, power_of_two in enumerate(POWERS_OF_TWO[:32]):
            if value & power_of_two:
                config.push_operand(UInt32(idx))
                break
        else:
            raise Exception("Invariant")


def i64ctz_op(config: Configuration) -> None:
    value = config.pop_u64()
    logger.debug("%s(%s)", config.instructions.current.opcode.text, value)

    if value == 0:
        config.push_operand(UInt64(64))
    else:
        for idx, power_of_two in enumerate(POWERS_OF_TWO):
            if value & power_of_two:
                config.push_operand(UInt64(idx))
                break
        else:
            raise Exception("Invariant")


#
# Count non-zero bits
#
def ipopcnt_op(config: Configuration) -> None:
    value = config.pop_operand()
    logger.debug("%s(%s)", config.instructions.current.opcode.text, value)

    if value == 0:
        config.push_operand(UInt32(0))
    else:
        config.push_operand(UInt32(bin(int(value)).count('1')))


#
# Remainders
#
def iremu_op(config: Configuration) -> None:
    b, a = config.pop2_u32()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if b == 0:
        raise Trap('DIVISION BY ZERO')

    config.push_operand(a % b)


def i32rems_op(config: Configuration) -> None:
    b, a = config.pop2_u32()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if b == 0:
        raise Trap('DIVISION BY ZERO')

    b_s = u32_to_s32(b)
    a_s = u32_to_s32(a)

    raw_result = abs(a_s) % abs(b_s)
    result = -1 * raw_result if a_s < 0 else raw_result

    config.push_operand(s32_to_u32(SInt32(int(result))))


def i64rems_op(config: Configuration) -> None:
    b, a = config.pop2_u64()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    if b == 0:
        raise Trap('DIVISION BY ZERO')

    b_s = u64_to_s64(b)
    a_s = u64_to_s64(a)

    raw_result = abs(a_s) % abs(b_s)
    result = -1 * raw_result if a_s < 0 else raw_result

    config.push_operand(s64_to_u64(SInt64(int(result))))


#
# Logical and/or/xor
#
def iand_op(config: Configuration) -> None:
    b, a = config.pop2_operands()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(UInt64(a & b))


def ior_op(config: Configuration) -> None:
    b, a = config.pop2_operands()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(UInt64(a | b))


def ixor_op(config: Configuration) -> None:
    b, a = config.pop2_operands()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(UInt64(a ^ b))


#
# Bitwise shifting
#
def i32shl_op(config: Configuration) -> None:
    b, a = config.pop2_u32()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(UInt32((a << (b % 32)) % constants.UINT32_CEIL))


def i64shl_op(config: Configuration) -> None:
    b, a = config.pop2_u64()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(UInt64((a << (b % 64)) % constants.UINT64_CEIL))


def i32shru_op(config: Configuration) -> None:
    b, a = config.pop2_u32()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(UInt32(a >> (b % 32)))


def i64shru_op(config: Configuration) -> None:
    b, a = config.pop2_u64()
    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(UInt64(a >> (b % 64)))


def i32shrs_op(config: Configuration) -> None:
    b, a = config.pop2_u32()

    a_s = u32_to_s32(a)

    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(UInt32(
        s32_to_u32(a_s >> (b % 32))
    ))


def i64shrs_op(config: Configuration) -> None:
    b, a = config.pop2_u64()

    a_s = u64_to_s64(a)

    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    config.push_operand(UInt64(
        s64_to_u64(a_s >> (b % 64))
    ))


#
# Bitwise rotation
#
def i32rotl_op(config: Configuration) -> None:
    b, a = config.pop2_u64()

    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    shift_size = b % 32
    upper = a << shift_size
    lower = a >> (32 - shift_size)

    config.push_operand(UInt32((upper | lower) % constants.UINT32_CEIL))


def i64rotl_op(config: Configuration) -> None:
    b, a = config.pop2_u64()

    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    shift_size = b % 64
    upper = a << shift_size
    lower = a >> (64 - shift_size)

    config.push_operand(UInt64((upper | lower) % constants.UINT64_CEIL))


def i32rotr_op(config: Configuration) -> None:
    b, a = config.pop2_u64()

    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    shift_size = b % 32
    lower = a >> shift_size
    upper = a << (32 - shift_size)

    config.push_operand(UInt32((upper | lower) % constants.UINT32_CEIL))


def i64rotr_op(config: Configuration) -> None:
    b, a = config.pop2_u64()

    logger.debug("%s(%s, %s)", config.instructions.current.opcode.text, a, b)

    shift_size = b % 64
    lower = a >> shift_size
    upper = a << (64 - shift_size)

    config.push_operand(UInt64((upper | lower) % constants.UINT64_CEIL))
