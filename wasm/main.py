import logging
import math
import struct
from typing import (
    Callable,
    Dict,
    Tuple,
    Union,
    cast,
)

from wasm import (
    constants,
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
    Demote,
    Extend,
    Promote,
    Reinterpret,
    RelOp,
    TestOp,
    Truncate,
    Wrap,
)
from wasm.opcodes import (
    BinaryOpcode,
)

logger = logging.getLogger('wasm.spec')


###############
###############
# 2 STRUCTURE #
###############
###############

# Chapter 2 defines the abstract syntax, which is used throughout the
# implementation. Not much is needed from this section, since most abstrct
# syntax is nested lists and dictionaries

# 2.2.3 FLOATING-POINT

# functions in this sectio are not currently used since we decided to use
# native Python floats, and struct.pack()/unpack() to encode/decode, but we may
# use these later to pass the rest of the NaN tests


def spec_expon(N):
    logging.debug("spec_expon(%s)", N)

    if N == 32:
        return 8
    elif N == 64:
        return 11
    else:
        raise Exception(f"Invariant: got '{N}' | expected one of 32/64")


# 2.3.8 EXTERNAL TYPES


# 2.5.10.1 EXTERNAL TYPES


################
################
# 3 VALIDATION #
################
################

# Chapter 3 defines validation rules over the abstract syntax. These rules
# constrain the syntax, but provide properties such as type-safety. An
# almost-complete implementation is available as a feature-branch.


###########
# 3.2 TYPES
###########

# 3.2.1 LIMITS


# 3.2.2 FUNCTION TYPES


# 3.2.3 TABLE TYPES


# 3.2.4 MEMORY TYPES


# 3.2.5 GLOBAL TYPES


##################
# 3.3 INSTRUCTIONS
##################

# 3.3.1 NUMERIC INSTRUCTIONS

# 3.3.2  PARAMETRIC INSTRUCTIONS

# 3.3.3 VARIABLE INSTRUCTIONS

# 3.3.4 MEMORY INSTRUCTIONS

# 3.3.5 CONTROL INSTRUCTIONS

# 3.3.6 INSTRUCTION SEQUENCES

# We use the algorithm in the appendix for validating instruction sequences

# 3.3.7 EXPRESSIONS


#############
# 3.4 MODULES
#############

# 3.4.1 FUNCTIONS


# 3.4.2 TABLES


# 3.4.3 MEMORIES


# 3.4.4 GLOBALS


# 3.4.5 ELEMENT SEGMENT


# 3.4.6 DATA SEGMENTS


# 3.4.7 START FUNCTION


# 3.4.8 EXPORTS


# 3.4.9 IMPORTS


# 3.4.10 MODULE


###############
###############
# 4 EXECUTION #
###############
###############

# Chapter 4 defines execution semantics over the abstract syntax.


##############
# 4.3 NUMERICS
##############


def spec_trunc(q):
    logger.debug("spec_trunc(%s)", q)

    # round towards zero
    # q can be float or rational as tuple (numerator,denominator)
    if type(q) == tuple:  # rational
        result = q[0] // q[1]  # rounds towards negative infinity
        if result < 0 and q[1] * result != q[0]:
            return result + 1
        else:
            return result
    elif type(q) == float:
        # using ftrunc instead
        return int(q)


# 4.3.1 REPRESENTATIONS

# bits are string of 1s and 0s
# bytes are bytearray (maybe can also read from memoryview)


def spec_bitst(valtype: ValType, c: int) -> str:
    logger.debug("spec_bitst(%s, %s)", valtype, c)

    N = valtype.bit_size.value

    if valtype.is_integer_type:
        return spec_bitsiN(N, c)
    elif valtype.is_float_type:
        return spec_bitsfN(N, c)
    else:
        raise Exception(f"Invariant: unknown type '{valtype}'")


def spec_bitst_inv(t, bits):
    logger.debug("spec_bitst_inv(%s, %s)", t, bits)

    N = t.bit_size.value

    if t.is_integer_type:
        return spec_bitsiN_inv(N, bits)
    elif t.is_float_type:
        return spec_bitsfN_inv(N, bits)
    else:
        raise Exception(f"Invariant: unknown type '{t}'")


def spec_bitsiN(N: int, i: int) -> str:
    logger.debug("spec_bitsiN(%s, %s)", N, i)

    return spec_ibitsN(N, i)


def spec_bitsiN_inv(N, bits):
    logger.debug("spec_bitsiN_inv(%s, %s)", N, bits)

    return spec_ibitsN_inv(N, bits)


def spec_bitsfN(N, z):
    logger.debug("spec_bitsfN(%s, %s)", N, z)

    return spec_fbitsN(N, z)


def spec_bitsfN_inv(N, bits):
    logger.debug("spec_bitsfN_inv(%s, %s)", N, bits)

    return spec_fbitsN_inv(N, bits)


# Integers


def spec_ibitsN(N: int, i: int) -> str:
    logger.debug("spec_ibitsN(%s, %s)", N, i)

    return bin(i)[2:].zfill(N)


def spec_ibitsN_inv(N: int, bits: str) -> int:
    logger.debug("spec_ibitsN_inv(%s, %s)", N, bits)

    return int(bits, 2)


# Floating-Point


def spec_fbitsN(N, z):
    logger.debug("spec_fbitsN(%s, %s)", N, z)

    if N == 32:
        z_bytes = struct.pack(">f", z)
    elif N == 64:
        z_bytes = struct.pack(">d", z)
    else:
        raise Exception(f"Invariant: bit size must be one of 32/64 - Got '{N}'")

    # stryct.pack() gave us bytes, need bits
    bits = ""
    for byte in z_bytes:
        bits += bin(int(byte)).lstrip("0b").zfill(8)
    return bits


def spec_fbitsN_inv(N, bits):
    logger.debug("spec_fbitsN_inv(%s, %s)", N, bits)

    # will use struct.unpack() so need bytearray
    bytes_ = bytearray()
    for i in range(len(bits) // 8):
        bytes_ += bytearray([int(bits[8 * i:8 * (i + 1)], 2)])
    if N == 32:
        z = struct.unpack(">f", bytes_)[0]
    elif N == 64:
        z = struct.unpack(">d", bytes_)[0]
    else:
        raise Exception(f"Invariant: N must be one of 32/64 - Got '{N}'")
    return z


def spec_fsign(z):
    logger.debug("spec_fsign(%s)", z)

    bytes_ = spec_bytest(ValType.f64, z)
    sign = bytes_[-1] & 0b10000000  # -1 since littleendian
    if sign:
        return 1
    else:
        return 0


# decided to just use struct.pack() and struct.unpack()
# other options to represent floating point numbers:
#   float which is 64-bit, for 32-bit, can truncate significand and exponent after each operation
#   ctypes.c_float and ctypes.c_double
#   numpy.float32 and numpy.float64


# Storage


def spec_bytest(valtype: ValType, i: int) -> bytearray:
    logger.debug("spec_bytest(%s, %s)", valtype, i)

    N = valtype.bit_size.value

    if valtype.is_integer_type:
        bits = spec_bitsiN(N, i)
    elif valtype.is_float_type:
        bits = spec_bitsfN(N, i)
    else:
        raise Exception(f"Invariant: unknown type '{valtype}'")

    return spec_littleendian(bits)


def spec_bytest_inv(valtype: ValType, bytes_: bytes) -> bytearray:
    logger.debug("spec_bytest_inv(%s, %s)", valtype, bytes_)

    bits = spec_littleendian_inv(bytes_)

    if valtype.is_integer_type:
        return spec_bitsiN_inv(valtype.bit_size.value, bits)
    elif valtype.is_float_type:
        return spec_bitsfN_inv(valtype.bit_size.value, bits)
    else:
        raise Exception(f"Invariant: unknown type '{valtype}'")


def spec_littleendian(d):
    logger.debug("spec_littleendian(%s)", d)

    # same behavior for both 32 and 64-bit values
    # this assumes len(d) is divisible by 8
    if len(d) == 0:
        return bytearray()
    d18 = d[:8]
    d2Nm8 = d[8:]
    d18_as_int = spec_ibitsN_inv(8, d18)
    return spec_littleendian(d2Nm8) + bytearray([d18_as_int])


def spec_littleendian_inv(bytes_):
    logger.debug("spec_littleendian_inv(%s)", bytes_)

    # same behavior for both 32 and 64-bit values
    # this assumes len(d) is divisible by 8
    # this converts bytes to bits
    if len(bytes_) == 0:
        return ""
    bits = bin(int(bytes_[-1])).lstrip("0b").zfill(8)
    return bits + spec_littleendian_inv(bytes_[:-1])


# 4.3.2 INTEGER OPERATIONS


# two's comlement
def spec_signediN(N, i):
    """
    TODO: see if this is faster
    return i - int((i << 1) & 2**N) #https://stackoverflow.com/a/36338336
    """
    logger.debug("spec_signediN(%s, %s)", N, i)

    if 0 <= i < 2 ** (N - 1):
        return i
    elif 2 ** (N - 1) <= i < 2 ** N:
        return i - 2 ** N
    else:
        raise Exception(f"Invariant: bit size out of range - Got '{N}'")


def spec_signediN_inv(N, i):
    logger.debug("spec_signediN_inv(%s, %s)", N, i)

    if 0 <= i < 2 ** (N - 1):
        return i
    elif -1 * (2 ** (N - 1)) <= i < 0:
        return i + 2 ** N
    else:
        raise Exception(f"Invariant: bit size out of range - Got '{N}'")


# 4.3.3 FLOATING-POINT OPERATIONS


def spec_fabsN(N, z):
    logger.debug("spec_fabsN(%s, %s)", N, z)

    sign = spec_fsign(z)
    if sign == 0:
        return z
    else:
        return spec_fnegN(N, z)


def spec_fnegN(N, z):
    logger.debug("spec_fnegN(%s, %s)", N, z)

    # get bytes and sign
    bytes_ = spec_bytest(ValType.f64, z)  # 64 since errors if z too bit for 32
    sign = spec_fsign(z)
    if sign == 0:
        bytes_[-1] |= 0b10000000  # -1 since littleendian
    else:
        bytes_[-1] &= 0b01111111  # -1 since littleendian
    z = spec_bytest_inv(ValType.f64, bytes_)  # 64 since errors if z too bit for 32
    return z


def spec_fceilN(N, z):
    logger.debug("spec_fceilN(%s, %s)", N, z)

    if math.isnan(z):
        return z
    elif math.isinf(z):
        return z
    elif z == 0:
        return z
    elif -1.0 < z < 0.0:
        return -0.0
    else:
        return float(math.ceil(z))


def spec_ffloorN(N, z):
    logger.debug("spec_ffloorN(%s, %s)", N, z)

    if math.isnan(z):
        return z
    elif math.isinf(z):
        return z
    elif z == 0:
        return z
    elif 0.0 < z < 1.0:
        return 0.0
    else:
        return float(math.floor(z))


def spec_ftruncN(N, z):
    logger.debug("spec_ftruncN(%s, %s)", N, z)

    if math.isnan(z):
        return z
    elif math.isinf(z):
        return z
    elif z == 0:
        return z
    elif 0.0 < z < 1.0:
        return 0.0
    elif -1.0 < z < 0.0:
        return -0.0
    else:
        magnitude = spec_fabsN(N, z)
        floormagnitude = spec_ffloorN(N, magnitude)
        return floormagnitude * (
            -1 if spec_fsign(z) else 1
        )  # math.floor(z)) + spec_fsign(z)


def spec_fnearestN(N, z):
    logger.debug("spec_fnearestN(%s, %s)", N, z)

    if math.isnan(z):
        return z
    elif math.isinf(z):
        return z
    elif z == 0:
        return z
    elif 0.0 < z <= 0.5:
        return 0.0
    elif -0.5 <= z < 0.0:
        return -0.0
    else:
        return float(round(z))


def spec_fsqrtN(N, z):
    logger.debug("spec_fsqrtN(%s, %s)", N, z)

    if math.isnan(z) or (z != 0 and spec_fsign(z) == 1):
        return math.nan
    else:
        return math.sqrt(z)


def spec_faddN(N, z1, z2):
    logger.debug("spec_faddN(%s, %s, %s)", N, z1, z2)

    res = z1 + z2
    if N == 32:
        res = spec_demoteMN(64, 32, res)
    return res


def spec_fsubN(N, z1, z2):
    logger.debug("spec_fsubN(%s, %s, %s)", N, z1, z2)

    res = z1 - z2
    if N == 32:
        res = spec_demoteMN(64, 32, res)
    return res


def spec_fmulN(N, z1, z2):
    logger.debug("spec_fmulN(%s, %s, %s)", N, z1, z2)

    res = z1 * z2
    if N == 32:
        res = spec_demoteMN(64, 32, res)
    return res


def spec_fdivN(N, z1, z2):
    logger.debug("spec_fdivN(%s, %s, %s)", N, z1, z2)

    if math.isnan(z1):
        return z1
    elif math.isnan(z2):
        return z2
    elif math.isinf(z1) and math.isinf(z2):
        return math.nan
    elif z1 == 0.0 and z2 == 0.0:
        return math.nan
    elif z1 == 0.0 and z2 == 0.0:
        return math.nan
    elif math.isinf(z1):
        if spec_fsign(z1) == spec_fsign(z2):
            return math.inf
        else:
            return -math.inf
    elif math.isinf(z2):
        if spec_fsign(z1) == spec_fsign(z2):
            return 0.0
        else:
            return -0.0
    elif z1 == 0:
        if spec_fsign(z1) == spec_fsign(z2):
            return 0.0
        else:
            return -0.0
    elif z2 == 0:
        if spec_fsign(z1) == spec_fsign(z2):
            return math.inf
        else:
            return -math.inf
    else:
        res = z1 / z2
        if N == 32:
            res = spec_demoteMN(64, 32, res)
        return res


def spec_fminN(N, z1, z2):
    logger.debug("spec_fminN(%s, %s, %s)", N, z1, z2)

    if math.isnan(z1):
        return z1
    elif math.isnan(z2):
        return z2
    elif z1 == -math.inf or z2 == -math.inf:
        return -math.inf
    elif z1 == math.inf:
        return z2
    elif z2 == math.inf:
        return z1
    elif z1 == z2 == 0.0:
        if spec_fsign(z1) != spec_fsign(z2):
            return -0.0
        else:
            return z1
    elif z1 <= z2:
        return z1
    else:
        return z2


def spec_fmaxN(N, z1, z2):
    logger.debug("spec_fmaxN(%s, %s, %s)", N, z1, z2)

    if math.isnan(z1):
        return z1
    elif math.isnan(z2):
        return z2
    elif z1 == math.inf or z2 == math.inf:
        return math.inf
    elif z1 == -math.inf:
        return z2
    elif z2 == -math.inf:
        return z1
    elif z1 == z2 == 0.0:
        if spec_fsign(z1) != spec_fsign(z2):
            return 0.0
        else:
            return z1
    elif z1 <= z2:
        return z2
    else:
        return z1


def spec_fcopysignN(N, z1, z2):
    logger.debug("spec_fcopysignN(%s, %s, %s)", N, z1, z2)

    z1sign = spec_fsign(z1)
    z2sign = spec_fsign(z2)
    if z1sign == z2sign:
        return z1
    else:
        z1bytes = spec_bytest(ValType.get_float_type(N), z1)
        if z1sign == 0:
            z1bytes[-1] |= 0b10000000  # -1 since littleendian
        else:
            z1bytes[-1] &= 0b01111111  # -1 since littleendian
        z1 = spec_bytest_inv(ValType.get_float_type(N), z1bytes)
        return z1


# 4.3.4 CONVERSIONS


def spec_extend_uMN(M, N, i):
    logger.debug("spec_extend_uMN(%s, %s, %s)", M, N, i)

    # TODO: confirm this implementation is correct.
    return i


def spec_extend_sMN(M, N, i):
    logger.debug("spec_extend_sMN(%s, %s, %s)", M, N, i)

    j = spec_signediN(M, i)
    return spec_signediN_inv(N, j)


def spec_wrapMN(M, N, i):
    logger.debug("spec_wrapMN(%s, %s, %s)", M, N, i)

    return i % (2 ** N)


def spec_trunc_uMN(M, N, z):
    logger.debug("spec_trunc_uMN(%s, %s, %s)", M, N, z)

    if math.isnan(z) or math.isinf(z):
        raise Trap("trap")

    ztrunc = spec_ftruncN(M, z)

    if -1 < ztrunc < 2 ** N:
        return int(ztrunc)
    else:
        raise Trap("trap")


def spec_trunc_sMN(M, N, z):
    logger.debug("spec_trunc_sMN(%s, %s, %s)", M, N, z)

    if math.isnan(z) or math.isinf(z):
        raise Trap("trap")

    ztrunc = spec_ftruncN(M, z)

    if -(2 ** (N - 1)) - 1 < ztrunc < 2 ** (N - 1):
        iztrunc = int(ztrunc)
        if iztrunc < 0:
            return spec_signediN_inv(N, iztrunc)
        else:
            return iztrunc
    else:
        raise Trap("trap")


def spec_promoteMN(M, N, z):
    logger.debug("spec_promoteMN(%s, %s, %s)", M, N, z)

    # TODO: confirm this implementation is correct.
    return z


def spec_demoteMN(M, N, z):
    logger.debug("spec_demoteMN(%s, %s, %s)", M, N, z)

    absz = spec_fabsN(N, z)
    # limitN = 2**(2**(spec_expon(N)-1))
    # TODO: confirm this implementation is correct.
    limitN = constants.UINT128_CEIL * (
        1 - 2 ** -25
    )  # this FLT_MAX is slightly different than the Wasm spec's 2**127
    if absz >= limitN:
        signz = spec_fsign(z)
        if signz:
            return -math.inf
        else:
            return math.inf
    bytes_ = spec_bytest(ValType.f32, z)
    z32 = spec_bytest_inv(ValType.f32, bytes_)
    return z32


def spec_convert_uMN(M, N, i):
    logger.debug("spec_convert_uMN(%s, %s, %s)", M, N, i)

    limitN = 2 ** (2 ** (spec_expon(N) - 1))
    if i >= limitN:
        return math.inf
    return float(i)


def spec_convert_sMN(M, N, i):
    logger.debug("spec_convert_sMN(%s, %s, %s)", M, N, i)

    limitN = 2 ** (2 ** (spec_expon(N) - 1))

    if i >= limitN:
        return math.inf
    elif i <= -1 * limitN:
        return -math.inf
    else:
        i = spec_signediN(M, i)
        return float(i)


def spec_reinterprett1t2(t1, t2, c):
    logger.debug("spec_reinterprett1t2(%s, %s, %s)", t1, t2, c)

    bits = spec_bitst(t1, c)
    return spec_bitst_inv(t2, bits)


##################
# 4.4 INSTRUCTIONS
##################

# S is the store

# 4.4.1 NUMERIC INSTRUCTIONS


def spec_tunop(config: Configuration) -> None:
    logger.debug("spec_tunop()")

    instruction = cast(BinOp, config.instructions.current)
    t = instruction.valtype
    op = opcode2exec[instruction.opcode][1]
    c1 = config.pop_operand()
    c = op(t.bit_size.value, c1)

    config.push_operand(c)


def spec_tbinop(config: Configuration) -> None:
    logger.debug("spec_tbinop()")

    instruction = cast(BinOp, config.instructions.current)
    t = instruction.valtype
    op = opcode2exec[instruction.opcode][1]
    c2, c1 = config.pop2_operands()
    c = op(t.bit_size.value, c1, c2)

    config.push_operand(c)


def spec_ttestop(config: Configuration) -> None:
    logger.debug("spec_ttestop()")

    instruction = cast(TestOp, config.instructions.current)
    t = instruction.valtype
    op = opcode2exec[instruction.opcode][1]
    c1 = config.pop_operand()
    c = op(t.bit_size.value, c1)

    config.push_operand(c)


def spec_trelop(config: Configuration) -> None:
    logger.debug("spec_trelop()")

    instruction = cast(RelOp, config.instructions.current)
    t = instruction.valtype
    op = opcode2exec[instruction.opcode][1]
    c2, c1 = config.pop2_operands()
    c = op(t.bit_size.value, c1, c2)

    config.push_operand(c)


T_t2cvt = Union[Wrap, Truncate, Extend, Demote, Promote, Convert, Reinterpret]


def spec_t2cvtopt1(config: Configuration) -> None:
    logger.debug("spec_t2cvtopt1()")

    instruction = cast(T_t2cvt, config.instructions.current)
    t2 = instruction.valtype
    t1 = instruction.result
    op = opcode2exec[instruction.opcode][1]
    c1 = config.pop_operand()

    if instruction.opcode.is_reinterpret:
        c2 = op(t1, t2, c1)
    else:
        c2 = op(t1.bit_size.value, t2.bit_size.value, c1)

    config.push_operand(c2)


# 4.4.2 PARAMETRIC INSTRUCTIONS


# 4.4.3 VARIABLE INSTRUCTIONS


# 4.4.4 MEMORY INSTRUCTIONS


# 4.4.5 CONTROL INSTRUCTIONS


# 4.4.6 BLOCKS


# 4.4.7 FUNCTION CALLS


# 4.4.8 EXPRESSIONS


# Map each opcode to the function(s) to invoke when it is encountered. For
# opcodes with two functions, the second function is called by the first
# function.
opcode2exec: Dict[BinaryOpcode, Tuple[Callable, ...]] = {
    # BinaryOpcode.UNREACHABLE: (spec_unreachable,),
    # BinaryOpcode.NOP: (spec_nop,),
    # BinaryOpcode.BLOCK: (spec_block,),  # blocktype in* end
    # BinaryOpcode.LOOP: (spec_loop,),  # blocktype in* end
    # BinaryOpcode.IF: (spec_if,),  # blocktype in1* else? in2* end
    # BinaryOpcode.ELSE: (spec_end,),  # in2*
    # BinaryOpcode.END: (spec_end,),
    # BinaryOpcode.BR: (spec_br,),  # labelidx
    # BinaryOpcode.BR_IF: (spec_br_if,),  # labelidx
    # BinaryOpcode.BR_TABLE: (spec_br_table,),  # labelidx* labelidx
    # BinaryOpcode.RETURN: (spec_return,),
    # BinaryOpcode.CALL: (spec_call,),  # funcidx
    # BinaryOpcode.CALL_INDIRECT: (spec_call_indirect,),  # typeidx 0x00
    # BinaryOpcode.DROP: (spec_drop,),
    # BinaryOpcode.SELECT: (spec_select,),
    # BinaryOpcode.GET_LOCAL: (spec_get_local,),  # localidx
    # BinaryOpcode.SET_LOCAL: (spec_set_local,),  # localidx
    # BinaryOpcode.TEE_LOCAL: (spec_tee_local,),  # localidx
    # BinaryOpcode.GET_GLOBAL: (spec_get_global,),  # globalidx
    # BinaryOpcode.SET_GLOBAL: (spec_set_global,),  # globalidx
    # BinaryOpcode.I32_LOAD: (spec_tload,),  # memarg
    # BinaryOpcode.I64_LOAD: (spec_tload,),  # memarg
    # BinaryOpcode.F32_LOAD: (spec_tload,),  # memarg
    # BinaryOpcode.F64_LOAD: (spec_tload,),  # memarg
    # BinaryOpcode.I32_LOAD8_S: (spec_tload,),  # memarg
    # BinaryOpcode.I32_LOAD8_U: (spec_tload,),  # memarg
    # BinaryOpcode.I32_LOAD16_S: (spec_tload,),  # memarg
    # BinaryOpcode.I32_LOAD16_U: (spec_tload,),  # memarg
    # BinaryOpcode.I64_LOAD8_S: (spec_tload,),  # memarg
    # BinaryOpcode.I64_LOAD8_U: (spec_tload,),  # memarg
    # BinaryOpcode.I64_LOAD16_S: (spec_tload,),  # memarg
    # BinaryOpcode.I64_LOAD16_U: (spec_tload,),  # memarg
    # BinaryOpcode.I64_LOAD32_S: (spec_tload,),  # memarg
    # BinaryOpcode.I64_LOAD32_U: (spec_tload,),  # memarg
    # BinaryOpcode.I32_STORE: (spec_tstore,),  # memarg
    # BinaryOpcode.I64_STORE: (spec_tstore,),  # memarg
    # BinaryOpcode.F32_STORE: (spec_tstore,),  # memarg
    # BinaryOpcode.F64_STORE: (spec_tstore,),  # memarg
    # BinaryOpcode.I32_STORE8: (spec_tstore,),  # memarg
    # BinaryOpcode.I32_STORE16: (spec_tstore,),  # memarg
    # BinaryOpcode.I64_STORE8: (spec_tstore,),  # memarg
    # BinaryOpcode.I64_STORE16: (spec_tstore,),  # memarg
    # BinaryOpcode.I64_STORE32: (spec_tstore,),  # memarg
    # BinaryOpcode.MEMORY_SIZE: (spec_memorysize,),
    # BinaryOpcode.MEMORY_GROW: (spec_memorygrow,),
    # BinaryOpcode.I32_CONST: (spec_tconst,),  # i32
    # BinaryOpcode.I64_CONST: (spec_tconst,),  # i64
    # BinaryOpcode.F32_CONST: (spec_tconst,),  # f32
    # BinaryOpcode.F64_CONST: (spec_tconst,),  # f64
    # BinaryOpcode.I32_EQZ: (spec_ttestop, spec_ieqzN),
    # BinaryOpcode.I32_EQ: (spec_trelop, spec_ieqN),
    # BinaryOpcode.I32_NE: (spec_trelop, spec_ineN),
    # BinaryOpcode.I32_LT_S: (spec_trelop, spec_ilt_sN),
    # BinaryOpcode.I32_LT_U: (spec_trelop, spec_ilt_uN),
    # BinaryOpcode.I32_GT_S: (spec_trelop, spec_igt_sN),
    # BinaryOpcode.I32_GT_U: (spec_trelop, spec_igt_uN),
    # BinaryOpcode.I32_LE_S: (spec_trelop, spec_ile_sN),
    # BinaryOpcode.I32_LE_U: (spec_trelop, spec_ile_uN),
    # BinaryOpcode.I32_GE_S: (spec_trelop, spec_ige_sN),
    # BinaryOpcode.I32_GE_U: (spec_trelop, spec_ige_uN),
    # BinaryOpcode.I64_EQZ: (spec_ttestop, spec_ieqzN),
    # BinaryOpcode.I64_EQ: (spec_trelop, spec_ieqN),
    # BinaryOpcode.I64_NE: (spec_trelop, spec_ineN),
    # BinaryOpcode.I64_LT_S: (spec_trelop, spec_ilt_sN),
    # BinaryOpcode.I64_LT_U: (spec_trelop, spec_ilt_uN),
    # BinaryOpcode.I64_GT_S: (spec_trelop, spec_igt_sN),
    # BinaryOpcode.I64_GT_U: (spec_trelop, spec_igt_uN),
    # BinaryOpcode.I64_LE_S: (spec_trelop, spec_ile_sN),
    # BinaryOpcode.I64_LE_U: (spec_trelop, spec_ile_uN),
    # BinaryOpcode.I64_GE_S: (spec_trelop, spec_ige_sN),
    # BinaryOpcode.I64_GE_U: (spec_trelop, spec_ige_uN),
    # BinaryOpcode.F32_EQ: (spec_trelop, spec_feqN),
    # BinaryOpcode.F32_NE: (spec_trelop, spec_fneN),
    # BinaryOpcode.F32_LT: (spec_trelop, spec_fltN),
    # BinaryOpcode.F32_GT: (spec_trelop, spec_fgtN),
    # BinaryOpcode.F32_LE: (spec_trelop, spec_fleN),
    # BinaryOpcode.F32_GE: (spec_trelop, spec_fgeN),
    # BinaryOpcode.F64_EQ: (spec_trelop, spec_feqN),
    # BinaryOpcode.F64_NE: (spec_trelop, spec_fneN),
    # BinaryOpcode.F64_LT: (spec_trelop, spec_fltN),
    # BinaryOpcode.F64_GT: (spec_trelop, spec_fgtN),
    # BinaryOpcode.F64_LE: (spec_trelop, spec_fleN),
    # BinaryOpcode.F64_GE: (spec_trelop, spec_fgeN),
    # BinaryOpcode.I32_CLZ: (spec_tunop, spec_iclzN),
    # BinaryOpcode.I32_CTZ: (spec_tunop, spec_ictzN),
    # BinaryOpcode.I32_POPCNT: (spec_tunop, spec_ipopcntN),
    # BinaryOpcode.I32_ADD: (spec_tbinop, spec_iaddN),
    # BinaryOpcode.I32_SUB: (spec_tbinop, spec_isubN),
    # BinaryOpcode.I32_MUL: (spec_tbinop, spec_imulN),
    # BinaryOpcode.I32_DIV_S: (spec_tbinop, spec_idiv_sN),
    # BinaryOpcode.I32_DIV_U: (spec_tbinop, spec_idiv_uN),
    # BinaryOpcode.I32_REM_S: (spec_tbinop, spec_irem_sN),
    # BinaryOpcode.I32_REM_U: (spec_tbinop, spec_irem_uN),
    # BinaryOpcode.I32_AND: (spec_tbinop, spec_iandN),
    # BinaryOpcode.I32_OR: (spec_tbinop, spec_iorN),
    # BinaryOpcode.I32_XOR: (spec_tbinop, spec_ixorN),
    # BinaryOpcode.I32_SHL: (spec_tbinop, spec_ishlN),
    # BinaryOpcode.I32_SHR_S: (spec_tbinop, spec_ishr_sN),
    # BinaryOpcode.I32_SHR_U: (spec_tbinop, spec_ishr_uN),
    # BinaryOpcode.I32_ROTL: (spec_tbinop, spec_irotlN),
    # BinaryOpcode.I32_ROTR: (spec_tbinop, spec_irotrN),
    # BinaryOpcode.I64_CLZ: (spec_tunop, spec_iclzN),
    # BinaryOpcode.I64_CTZ: (spec_tunop, spec_ictzN),
    # BinaryOpcode.I64_POPCNT: (spec_tunop, spec_ipopcntN),
    # BinaryOpcode.I64_ADD: (spec_tbinop, spec_iaddN),
    # BinaryOpcode.I64_SUB: (spec_tbinop, spec_isubN),
    # BinaryOpcode.I64_MUL: (spec_tbinop, spec_imulN),
    # BinaryOpcode.I64_DIV_S: (spec_tbinop, spec_idiv_sN),
    # BinaryOpcode.I64_DIV_U: (spec_tbinop, spec_idiv_uN),
    # BinaryOpcode.I64_REM_S: (spec_tbinop, spec_irem_sN),
    # BinaryOpcode.I64_REM_U: (spec_tbinop, spec_irem_uN),
    # BinaryOpcode.I64_AND: (spec_tbinop, spec_iandN),
    # BinaryOpcode.I64_OR: (spec_tbinop, spec_iorN),
    # BinaryOpcode.I64_XOR: (spec_tbinop, spec_ixorN),
    # BinaryOpcode.I64_SHL: (spec_tbinop, spec_ishlN),
    # BinaryOpcode.I64_SHR_S: (spec_tbinop, spec_ishr_sN),
    # BinaryOpcode.I64_SHR_U: (spec_tbinop, spec_ishr_uN),
    # BinaryOpcode.I64_ROTL: (spec_tbinop, spec_irotlN),
    # BinaryOpcode.I64_ROTR: (spec_tbinop, spec_irotrN),
    BinaryOpcode.F32_ABS: (spec_tunop, spec_fabsN),
    BinaryOpcode.F32_NEG: (spec_tunop, spec_fnegN),
    BinaryOpcode.F32_CEIL: (spec_tunop, spec_fceilN),
    BinaryOpcode.F32_FLOOR: (spec_tunop, spec_ffloorN),
    BinaryOpcode.F32_TRUNC: (spec_tunop, spec_ftruncN),
    BinaryOpcode.F32_NEAREST: (spec_tunop, spec_fnearestN),
    BinaryOpcode.F32_SQRT: (spec_tunop, spec_fsqrtN),
    BinaryOpcode.F32_ADD: (spec_tbinop, spec_faddN),
    BinaryOpcode.F32_SUB: (spec_tbinop, spec_fsubN),
    BinaryOpcode.F32_MUL: (spec_tbinop, spec_fmulN),
    BinaryOpcode.F32_DIV: (spec_tbinop, spec_fdivN),
    BinaryOpcode.F32_MIN: (spec_tbinop, spec_fminN),
    BinaryOpcode.F32_MAX: (spec_tbinop, spec_fmaxN),
    BinaryOpcode.F32_COPYSIGN: (spec_tbinop, spec_fcopysignN),
    BinaryOpcode.F64_ABS: (spec_tunop, spec_fabsN),
    BinaryOpcode.F64_NEG: (spec_tunop, spec_fnegN),
    BinaryOpcode.F64_CEIL: (spec_tunop, spec_fceilN),
    BinaryOpcode.F64_FLOOR: (spec_tunop, spec_ffloorN),
    BinaryOpcode.F64_TRUNC: (spec_tunop, spec_ftruncN),
    BinaryOpcode.F64_NEAREST: (spec_tunop, spec_fnearestN),
    BinaryOpcode.F64_SQRT: (spec_tunop, spec_fsqrtN),
    BinaryOpcode.F64_ADD: (spec_tbinop, spec_faddN),
    BinaryOpcode.F64_SUB: (spec_tbinop, spec_fsubN),
    BinaryOpcode.F64_MUL: (spec_tbinop, spec_fmulN),
    BinaryOpcode.F64_DIV: (spec_tbinop, spec_fdivN),
    BinaryOpcode.F64_MIN: (spec_tbinop, spec_fminN),
    BinaryOpcode.F64_MAX: (spec_tbinop, spec_fmaxN),
    BinaryOpcode.F64_COPYSIGN: (spec_tbinop, spec_fcopysignN),
    BinaryOpcode.I32_WRAP_I64: (spec_t2cvtopt1, spec_wrapMN),
    BinaryOpcode.I32_TRUNC_S_F32: (spec_t2cvtopt1, spec_trunc_sMN),
    BinaryOpcode.I32_TRUNC_U_F32: (spec_t2cvtopt1, spec_trunc_uMN),
    BinaryOpcode.I32_TRUNC_S_F64: (spec_t2cvtopt1, spec_trunc_sMN),
    BinaryOpcode.I32_TRUNC_U_F64: (spec_t2cvtopt1, spec_trunc_uMN),
    BinaryOpcode.I64_EXTEND_S_I32: (spec_t2cvtopt1, spec_extend_sMN),
    BinaryOpcode.I64_EXTEND_U_I32: (spec_t2cvtopt1, spec_extend_uMN),
    BinaryOpcode.I64_TRUNC_S_F32: (spec_t2cvtopt1, spec_trunc_sMN),
    BinaryOpcode.I64_TRUNC_U_F32: (spec_t2cvtopt1, spec_trunc_uMN),
    BinaryOpcode.I64_TRUNC_S_F64: (spec_t2cvtopt1, spec_trunc_sMN),
    BinaryOpcode.I64_TRUNC_U_F64: (spec_t2cvtopt1, spec_trunc_uMN),
    BinaryOpcode.F32_CONVERT_S_I32: (spec_t2cvtopt1, spec_convert_sMN),
    BinaryOpcode.F32_CONVERT_U_I32: (spec_t2cvtopt1, spec_convert_uMN),
    BinaryOpcode.F32_CONVERT_S_I64: (spec_t2cvtopt1, spec_convert_sMN),
    BinaryOpcode.F32_CONVERT_U_I64: (spec_t2cvtopt1, spec_convert_uMN),
    BinaryOpcode.F32_DEMOTE_F64: (spec_t2cvtopt1, spec_demoteMN),
    BinaryOpcode.F64_CONVERT_S_I32: (spec_t2cvtopt1, spec_convert_sMN),
    BinaryOpcode.F64_CONVERT_U_I32: (spec_t2cvtopt1, spec_convert_uMN),
    BinaryOpcode.F64_CONVERT_S_I64: (spec_t2cvtopt1, spec_convert_sMN),
    BinaryOpcode.F64_CONVERT_U_I64: (spec_t2cvtopt1, spec_convert_uMN),
    BinaryOpcode.F64_PROMOTE_F32: (spec_t2cvtopt1, spec_promoteMN),
    BinaryOpcode.I32_REINTERPRET_F32: (spec_t2cvtopt1, spec_reinterprett1t2),
    BinaryOpcode.I64_REINTERPRET_F64: (spec_t2cvtopt1, spec_reinterprett1t2),
    BinaryOpcode.F32_REINTERPRET_I32: (spec_t2cvtopt1, spec_reinterprett1t2),
    BinaryOpcode.F64_REINTERPRET_I64: (spec_t2cvtopt1, spec_reinterprett1t2),
}


#############
# 4.5 MODULES
#############

# 4.5.1 EXTERNAL TYPING


# 4.5.2 IMPORT MATCHING


# 4.5.3 ALLOCATION


# 4.5.5 INVOCATION

# valn looks like [["i32.const",3],["i32.const",199], ...]


###################
###################
# 5 BINARY FORMAT #
###################
###################

# Chapter 5 defines a binary syntax over the abstract syntax. The
# implementation is a recursive-descent parser which takes a `.wasm` file and
# builds an abstract syntax tree out of nested Python lists and dicts. Also
# implemented are inverses (up to a canonical form) which write an abstract
# syntax tree back to a `.wasm` file.


# 5.1.3 VECTORS


############
# 5.2 VALUES
############

# 5.2.1 BYTES


# 5.2.2 INTEGERS


# 5.2.3 FLOATING-POINT

# 5.2.4 NAMES


###########
# 5.3 TYPES
###########

# 5.3.1 VALUE TYPES


# 5.3.2 RESULT TYPES


# 5.3.3 FUNCTION TYPES


# 5.3.4 LIMITS


# 5.3.5 MEMORY TYPES


# 5.3.6 TABLE TYPES


# 5.3.7 GLOBAL TYPES


##################
# 5.4 INSTRUCTIONS
##################

# 5.4.1-5 VARIOUS INSTRUCTIONS


# 5.4.6 EXPRESSIONS


#############
# 5.5 MODULES
#############

# 5.5.1 INDICES


# 5.5.2 SECTIONS


# 5.5.3 CUSTOM SECTION


# 5.5.4 TYPE SECTION


# 5.5.5 IMPORT SECTION


# 5.5.6 FUNCTION SECTION


# 5.5.7 TABLE SECTION


# 5.5.8 MEMORY SECTION


# 5.5.9 GLOBAL SECTION


# 5.5.10 EXPORT SECTION


# 5.5.11 START SECTION


# 5.5.12 ELEMENT SECTION


# 5.5.13 CODE SECTION


# 5.5.14 DATA SECTION


# 5.5.15 MODULES


##############
##############
# 7 APPENDIX #
##############
##############

# Chapter 7 is the Appendix. It defines a standard embedding, and a validation algorithm.

###############
# 7.1 EMBEDDING
###############

# THE FOLLOWING IS THE API, HOPEFULLY NO FUNCTIONS ABOVE IS CALLED DIRECTLY

# 7.1.1 STORE


# 7.1.2 MODULES


# 7.1.3 EXPORTS


# 7.1.4 FUNCTIONS


# 7.1.4 TABLES


# 7.1.6 MEMORIES


# 7.1.7 GLOBALS
