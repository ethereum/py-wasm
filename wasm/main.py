import io
import logging
import math
import struct
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)

from wasm import (
    constants,
)
from wasm._utils.validation import (
    get_duplicates,
)
from wasm.datatypes import (
    Export,
    ExportInstance,
    Function,
    FunctionAddress,
    FunctionIdx,
    FunctionInstance,
    FunctionType,
    GlobalAddress,
    GlobalIdx,
    GlobalInstance,
    GlobalType,
    HostFunction,
    Import,
    LabelIdx,
    Limits,
    MemoryAddress,
    MemoryIdx,
    MemoryInstance,
    MemoryType,
    Module,
    ModuleInstance,
    Mutability,
    Store,
    TableAddress,
    TableIdx,
    TableInstance,
    TableType,
    TypeIdx,
    ValType,
)
from wasm.exceptions import (
    Exhaustion,
    InvalidModule,
    MalformedModule,
    ParseError,
    Trap,
    Unlinkable,
    ValidationError,
)
from wasm.execution import (
    Configuration,
    Frame,
    InstructionSequence,
    Label,
    OperandStack,
)
from wasm.instructions import (
    BaseInstruction,
    BinOp,
    Block,
    Br,
    BrIf,
    BrTable,
    Call,
    CallIndirect,
    Convert,
    Demote,
    End,
    Extend,
    GlobalOp,
    If,
    LocalOp,
    Loop,
    MemoryOp,
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
from wasm.parsers import (
    parse_module,
)
from wasm.typing import (
    Float32,
    HostFunctionCallable,
    TValue,
    UInt32,
)
from wasm.validation import (
    Context,
    validate_data_segment,
    validate_element_segment,
    validate_function,
    validate_function_type,
    validate_global,
    validate_memory,
    validate_memory_type,
    validate_start_function,
    validate_table,
    validate_table_type,
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

ExternType = Union[FunctionType, TableType, MemoryType, GlobalType]


def spec_funcs(imports: Iterable[ExternType]) -> Tuple[FunctionType, ...]:
    return tuple(item for item in imports if isinstance(item, FunctionType))


def spec_tables(imports: Iterable[ExternType]) -> Tuple[TableType, ...]:
    return tuple(item for item in imports if isinstance(item, TableType))


def spec_mems(imports: Iterable[ExternType]) -> Tuple[MemoryType, ...]:
    return tuple(item for item in imports if isinstance(item, MemoryType))


def spec_globals(imports: Iterable[ExternType]) -> Tuple[GlobalType, ...]:
    return tuple(item for item in imports if isinstance(item, GlobalType))


# 2.5.10.1 EXTERNAL TYPES

TExportAddress = Union[FunctionAddress, TableAddress, MemoryAddress, GlobalAddress]


def spec_funcs_exports(exports: Iterable[TExportAddress]) -> Tuple[FunctionAddress, ...]:
    return tuple(idx for idx in exports if isinstance(idx, FunctionAddress))


def spec_tables_exports(exports: Iterable[TExportAddress]) -> Tuple[TableAddress, ...]:
    return tuple(idx for idx in exports if isinstance(idx, TableAddress))


def spec_memory_exports(exports: Iterable[TExportAddress]) -> Tuple[MemoryAddress, ...]:
    return tuple(idx for idx in exports if isinstance(idx, MemoryAddress))


def spec_globals_exports(exports: Iterable[TExportAddress]) -> Tuple[GlobalAddress, ...]:
    return tuple(idx for idx in exports if isinstance(idx, GlobalAddress))


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


Expression = Tuple[BaseInstruction, ...]


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


TExportValue = Union[FunctionType, TableType, MemoryType, GlobalType]
TExportDesc = Union[FunctionIdx, GlobalIdx, MemoryIdx, TableIdx]


def spec_validate_export(context: Context, export: Export) -> TExportValue:
    return spec_validate_exportdesc(context, export.desc)


def spec_validate_exportdesc(context: Context,
                             idx: TExportDesc) -> TExportValue:
    if isinstance(idx, FunctionIdx):
        context.validate_function_idx(idx)
        return context.get_function(idx)
    elif isinstance(idx, TableIdx):
        context.validate_table_idx(idx)
        return context.get_table(idx)
    elif isinstance(idx, MemoryIdx):
        context.validate_mem_idx(idx)
        return context.get_mem(idx)
    elif isinstance(idx, GlobalIdx):
        context.validate_global_idx(idx)
        return context.get_global(idx)
    else:
        raise InvalidModule(f"Unknown export descriptor type: {type(idx)}")


def get_export_type(context: Context, idx: TExportDesc) -> TExportValue:
    if isinstance(idx, FunctionIdx):
        return context.get_function(idx)
    elif isinstance(idx, TableIdx):
        return context.get_table(idx)
    elif isinstance(idx, MemoryIdx):
        return context.get_mem(idx)
    elif isinstance(idx, GlobalIdx):
        return context.get_global(idx)
    else:
        raise InvalidModule(f"Unknown export descriptor type: {type(idx)}")


# 3.4.9 IMPORTS


TImport = Union[FunctionType, TableType, MemoryType, GlobalType]


def spec_validate_import(context: Context, import_: Import) -> None:
    spec_validate_importdesc(context, import_.desc)


TImportDesc = Union[TypeIdx, GlobalType, MemoryType, TableType]


def spec_validate_importdesc(context: Context, descriptor: TImportDesc) -> None:
    if isinstance(descriptor, TypeIdx):
        context.validate_type_idx(descriptor)
    elif isinstance(descriptor, TableType):
        validate_table_type(descriptor)
    elif isinstance(descriptor, MemoryType):
        validate_memory_type(descriptor)
    elif isinstance(descriptor, GlobalType):
        pass
    else:
        raise InvalidModule(f"Unknown import descriptor type: {type(descriptor)}")


def get_import_type(context: Context, descriptor: TImportDesc) -> TImport:
    if isinstance(descriptor, TypeIdx):
        return context.get_type(descriptor)
    elif isinstance(descriptor, (TableType, MemoryType, GlobalType)):
        return descriptor
    else:
        raise InvalidModule(f"Unknown import descriptor type: {type(descriptor)}")


# 3.4.10 MODULE


def spec_validate_module(module: Module) -> List[List[ExternType]]:
    # mod is the module to validate
    ftstar: List[FunctionType] = []

    for func in module.funcs:
        if len(module.types) <= func.type_idx:
            # this was not explicit in spec, how about other *tstar
            raise InvalidModule("invalid")
        ftstar += [module.types[func.type_idx]]

    ttstar = tuple(table.type for table in module.tables)
    mtstar = tuple(mem.type for mem in module.mems)
    gtstar = tuple(global_.type for global_ in module.globals)

    itstar: List[ExternType] = []
    for import_ in module.imports:
        if import_.is_function:
            if import_.type_idx >= len(module.types):
                # this was not explicit in spec
                raise InvalidModule(
                    f"Function import out of range: {import_.desc} > "
                    f"{len(module.types)}"
                )
            itstar.append(module.types[import_.type_idx])
        else:
            itstar.append(cast(Union[GlobalType, MemoryType, TableType], import_.desc))

    # let i_tstar be the concatenation of imports of each type
    iftstar = spec_funcs(itstar)
    ittstar = spec_tables(itstar)
    imtstar = spec_mems(itstar)
    igtstar = spec_globals(itstar)

    # let C and Cprime be contexts
    context = Context(
        types=module.types,
        functions=iftstar + tuple(ftstar),
        tables=ittstar + ttstar,
        mems=imtstar + mtstar,
        globals=igtstar + gtstar,
        locals=(),
        labels=(),
        returns=(),

    )

    # et* is needed later, here is a good place to do it
    etstar: List[ExternType] = []
    for export in module.exports:
        if export.is_function:
            if len(context.functions) <= export.desc:
                # this was not explicit in spec
                raise InvalidModule("invalid")
            etstar.append(context.functions[export.desc])
        elif export.is_table:
            if len(context.tables) <= export.desc:
                # this was not explicit in spec
                raise InvalidModule("invalid")
            etstar.append(context.tables[export.desc])
        elif export.is_memory:
            if len(context.mems) <= export.desc:
                # this was not explicit in spec
                raise InvalidModule("invalid")
            etstar.append(context.mems[export.desc])
        elif export.is_global:
            if len(context.globals) <= export.desc:
                # this was not explicit in spec
                raise InvalidModule("invalid")
            etstar.append(context.globals[export.desc])
        else:
            raise Exception(f"Invariant: Unknown export type: {type(export.desc)}")

    # under the context C
    for functypei in module.types:
        validate_function_type(functypei)

    for i, func in enumerate(module.funcs):
        validate_function(context, func, ftstar[i].results)

    for i, table in enumerate(module.tables):
        validate_table(table)
        if table.type != ttstar[i]:
            raise InvalidModule("invalid")

    for i, mem in enumerate(module.mems):
        validate_memory(mem)
        if mem.type != mtstar[i]:
            raise InvalidModule("invalid")

    global_context = Context(
        types=(),
        functions=(),
        tables=(),
        mems=(),
        globals=tuple(igtstar),
        locals=(),
        labels=(),
        returns=(),
    )
    for i, global_ in enumerate(module.globals):
        validate_global(global_context, global_)

    for elem in module.elem:
        validate_element_segment(context, elem)

    for data in module.data:
        validate_data_segment(context, data)

    if module.start is not None:
        validate_start_function(context, module.start)

    for i, import_ in enumerate(module.imports):
        spec_validate_import(context, import_)
        it = get_import_type(context, import_.desc)
        if it != itstar[i]:
            raise InvalidModule("invalid")

    for i, export in enumerate(module.exports):
        spec_validate_export(context, export)
        et = get_export_type(context, export.desc)
        if et != etstar[i]:
            raise InvalidModule("invalid")

    if len(context.tables) > 1:
        raise InvalidModule("invalid")
    elif len(context.mems) > 1:
        raise InvalidModule("invalid")

    # export names must be unique
    duplicate_exports: Tuple[str, ...] = get_duplicates(export.name for export in module.exports)
    if duplicate_exports:
        raise InvalidModule(
            "Duplicate module name(s) exported: "
            f"{'|'.join(sorted(duplicate_exports))}"
        )

    return [itstar, etstar]


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


def spec_iaddN(N, i1, i2):
    logger.debug("spec_iaddN(%s, %s, %s)", N, i1, i2)

    return (i1 + i2) % 2 ** N


def spec_isubN(N, i1, i2):
    logger.debug("spec_isubN(%s, %s, %s)", N, i1, i2)

    return (i1 - i2 + 2 ** N) % 2 ** N


def spec_imulN(N, i1, i2):
    logger.debug("spec_imulN(%s, %s, %s)", N, i1, i2)

    return (i1 * i2) % 2 ** N


def spec_idiv_uN(N, i1, i2):
    logger.debug("spec_idiv_uN(%s, %s, %s)", N, i1, i2)

    if i2 == 0:
        raise Trap("trap")
    return spec_trunc((i1, i2))


def spec_idiv_sN(N, i1, i2):
    logger.debug("spec_idiv_sN(%s, %s, %s)", N, i1, i2)

    j1 = spec_signediN(N, i1)
    j2 = spec_signediN(N, i2)
    if j2 == 0:
        raise Trap("trap")
    # assuming j1 and j2 are N-bit
    if j1 // j2 == 2 ** (N - 1):
        raise Trap("trap")
    return spec_signediN_inv(N, spec_trunc((j1, j2)))


def spec_irem_uN(N, i1, i2):
    logger.debug("spec_irem_uN(%s, %s, %s)", N, i1, i2)

    if i2 == 0:
        raise Trap("trap")
    return i1 - i2 * spec_trunc((i1, i2))


def spec_irem_sN(N, i1, i2):
    logger.debug("spec_irem_sN(%s, %s, %s)", N, i1, i2)

    j1 = spec_signediN(N, i1)
    j2 = spec_signediN(N, i2)
    if i2 == 0:
        raise Trap("trap")
    return spec_signediN_inv(N, j1 - j2 * spec_trunc((j1, j2)))


def spec_iandN(N, i1, i2):
    logger.debug("spec_iandN(%s, %s, %s)", N, i1, i2)

    return i1 & i2


def spec_iorN(N, i1, i2):
    logger.debug("spec_iorN(%s, %s, %s)", N, i1, i2)

    return i1 | i2


def spec_ixorN(N, i1, i2):
    logger.debug("spec_ixorN(%s, %s, %s)", N, i1, i2)

    return i1 ^ i2


def spec_ishlN(N, i1, i2):
    logger.debug("spec_ishlN(%s, %s, %s)", N, i1, i2)

    k = i2 % N
    return (i1 << k) % (2 ** N)


def spec_ishr_uN(N, i1, i2):
    logger.debug("spec_ishr_uN(%s, %s, %s)", N, i1, i2)

    j2 = i2 % N
    return i1 >> j2


def spec_ishr_sN(N, i1, i2):
    logger.debug("spec_ishr_sN(%s, %s, %s)", N, i1, i2)

    k = i2 % N
    d0d1Nmkm1d2k = spec_ibitsN(N, i1)
    d0 = d0d1Nmkm1d2k[0]
    d1Nmkm1 = d0d1Nmkm1d2k[1:N - k]
    return spec_ibitsN_inv(N, d0 * (k + 1) + d1Nmkm1)


def spec_irotlN(N, i1, i2):
    logger.debug("spec_irotlN(%s, %s, %s)", N, i1, i2)

    k = i2 % N
    d1kd2Nmk = spec_ibitsN(N, i1)
    d2Nmk = d1kd2Nmk[k:]
    d1k = d1kd2Nmk[:k]
    return spec_ibitsN_inv(N, d2Nmk + d1k)


def spec_irotrN(N, i1, i2):
    logger.debug("spec_irotrN(%s, %s, %s)", N, i1, i2)

    k = i2 % N
    d1Nmkd2k = spec_ibitsN(N, i1)
    d1Nmk = d1Nmkd2k[: N - k]
    d2k = d1Nmkd2k[N - k:]
    return spec_ibitsN_inv(N, d2k + d1Nmk)


def spec_iclzN(N, i):
    logger.debug("spec_iclzN(%s, %s)", N, i)

    k = 0
    for b in spec_ibitsN(N, i):
        if b == "0":
            k += 1
        else:
            break
    return k


def spec_ictzN(N, i):
    logger.debug("spec_ictzN(%s, %s)", N, i)

    k = 0
    for b in reversed(spec_ibitsN(N, i)):
        if b == "0":
            k += 1
        else:
            break
    return k


def spec_ipopcntN(N, i):
    logger.debug("spec_ipopcntN(%s, %s)", N, i)

    k = 0
    for b in spec_ibitsN(N, i):
        if b == "1":
            k += 1
    return k


def spec_ieqzN(N, i):
    logger.debug("spec_ieqzN(%s, %s)", N, i)

    if i == 0:
        return 1
    else:
        return 0


def spec_ieqN(N, i1, i2):
    logger.debug("spec_ieqN(%s, %s, %s)", N, i1, i2)

    if i1 == i2:
        return 1
    else:
        return 0


def spec_ineN(N, i1, i2):
    logger.debug("spec_ineN(%s, %s, %s)", N, i1, i2)

    if i1 != i2:
        return 1
    else:
        return 0


def spec_ilt_uN(N, i1, i2):
    logger.debug("spec_ilt_uN(%s, %s, %s)", N, i1, i2)

    if i1 < i2:
        return 1
    else:
        return 0


def spec_ilt_sN(N, i1, i2):
    logger.debug("spec_ilt_sN(%s, %s, %s)", N, i1, i2)

    j1 = spec_signediN(N, i1)
    j2 = spec_signediN(N, i2)
    if j1 < j2:
        return 1
    else:
        return 0


def spec_igt_uN(N, i1, i2):
    logger.debug("spec_igt_uN(%s, %s, %s)", N, i1, i2)

    if i1 > i2:
        return 1
    else:
        return 0


def spec_igt_sN(N, i1, i2):
    logger.debug("spec_igt_sN(%s, %s, %s)", N, i1, i2)

    j1 = spec_signediN(N, i1)
    j2 = spec_signediN(N, i2)
    if j1 > j2:
        return 1
    else:
        return 0


def spec_ile_uN(N, i1, i2):
    logger.debug("spec_ile_uN(%s, %s, %s)", N, i1, i2)

    if i1 <= i2:
        return 1
    else:
        return 0


def spec_ile_sN(N, i1, i2):
    logger.debug("spec_ile_sN(%s, %s, %s)", N, i1, i2)

    j1 = spec_signediN(N, i1)
    j2 = spec_signediN(N, i2)
    if j1 <= j2:
        return 1
    else:
        return 0


def spec_ige_uN(N, i1, i2):
    logger.debug("spec_ige_uN(%s, %s, %s)", N, i1, i2)

    if i1 >= i2:
        return 1
    else:
        return 0


def spec_ige_sN(N, i1, i2):
    logger.debug("spec_ige_sN(%s, %s, %s)", N, i1, i2)

    j1 = spec_signediN(N, i1)
    j2 = spec_signediN(N, i2)
    if j1 >= j2:
        return 1
    else:
        return 0


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


def spec_feqN(N, z1, z2):
    logger.debug("spec_feqN(%s, %s, %s)", N, z1, z2)

    if z1 == z2:
        return 1
    else:
        return 0


def spec_fneN(N, z1, z2):
    logger.debug("spec_fneN(%s, %s, %s)", N, z1, z2)

    if z1 != z2:
        return 1
    else:
        return 0


def spec_fltN(N, z1, z2):
    logger.debug("spec_fltN(%s, %s, %s)", N, z1, z2)

    if math.isnan(z1):
        return 0
    elif math.isnan(z2):
        return 0
    elif spec_bitsfN(N, z1) == spec_bitsfN(N, z2):
        return 0
    elif z1 == math.inf:
        return 0
    elif z1 == -math.inf:
        return 1
    elif z2 == math.inf:
        return 1
    elif z2 == -math.inf:
        return 0
    elif z1 == z2 == 0:
        return 0
    elif z1 < z2:
        return 1
    else:
        return 0


def spec_fgtN(N, z1, z2):
    logger.debug("spec_fgtN(%s, %s, %s)", N, z1, z2)

    if math.isnan(z1):
        return 0
    elif math.isnan(z2):
        return 0
    elif spec_bitsfN(N, z1) == spec_bitsfN(N, z2):
        return 0
    elif z1 == math.inf:
        return 1
    elif z1 == -math.inf:
        return 0
    elif z2 == math.inf:
        return 0
    elif z2 == -math.inf:
        return 1
    elif z1 == z2 == 0:
        return 0
    elif z1 > z2:
        return 1
    else:
        return 0


def spec_fleN(N, z1, z2):
    logger.debug("spec_fleN(%s, %s, %s)", N, z1, z2)

    if math.isnan(z1):
        return 0
    elif math.isnan(z2):
        return 0
    elif spec_bitsfN(N, z1) == spec_bitsfN(N, z2):
        return 1
    elif z1 == math.inf:
        return 0
    elif z1 == -math.inf:
        return 1
    elif z2 == math.inf:
        return 1
    elif z2 == -math.inf:
        return 0
    elif z1 == z2 == 0:
        return 1
    elif z1 <= z2:
        return 1
    else:
        return 0


def spec_fgeN(N, z1, z2):
    logger.debug("spec_fgeN(%s, %s, %s)", N, z1, z2)

    if math.isnan(z1):
        return 0
    elif math.isnan(z2):
        return 0
    elif spec_bitsfN(N, z1) == spec_bitsfN(N, z2):
        return 1
    elif z1 == math.inf:
        return 1
    elif z1 == -math.inf:
        return 0
    elif z2 == math.inf:
        return 0
    elif z2 == -math.inf:
        return 1
    elif z1 == z2 == 0:
        return 1
    elif z1 >= z2:
        return 1
    else:
        return 0


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


def spec_tconst(config):
    instruction = config.instructions.current
    value = instruction.value

    logger.debug("spec_tconst(%s)", value)

    config.push_operand(value)


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


def spec_drop(config: Configuration) -> None:
    logger.debug("spec_drop()")

    config.pop_operand()


def spec_select(config: Configuration) -> None:
    logger.debug("spec_select()")

    c, val1, val2 = config.pop3_operands()

    if c:
        config.push_operand(val2)
    else:
        config.push_operand(val1)


# 4.4.3 VARIABLE INSTRUCTIONS


def spec_get_local(config: Configuration) -> None:
    logger.debug("spec_get_local()")

    instruction = cast(LocalOp, config.instructions.current)
    val = config.frame.locals[instruction.local_idx]
    config.push_operand(val)


def spec_set_local(config: Configuration) -> None:
    logger.debug("spec_set_local()")

    instruction = cast(LocalOp, config.instructions.current)
    val = config.pop_operand()
    config.frame.locals[instruction.local_idx] = val


def spec_tee_local(config: Configuration) -> None:
    logger.debug("spec_tee_local()")

    val = config.pop_operand()
    config.push_operand(val)
    config.push_operand(val)
    spec_set_local(config)


def spec_get_global(config: Configuration) -> None:
    logger.debug("spec_get_global()")

    S = config.store
    instruction = cast(GlobalOp, config.instructions.current)
    a = config.frame.module.global_addrs[instruction.global_idx]
    glob = S.globals[a]
    config.push_operand(glob.value)


def spec_set_global(config):
    logger.debug("spec_set_global()")

    S = config.store
    instruction = cast(GlobalOp, config.instructions.current)
    a = config.frame.module.global_addrs[instruction.global_idx]
    glob = S.globals[a]
    if glob.mut is not Mutability.var:
        raise Exception("Attempt to set immutable global")
    val = config.pop_operand()
    S.globals[a] = GlobalInstance(glob.valtype, val, glob.mut)


# 4.4.4 MEMORY INSTRUCTIONS

# this is for both t.load and t.loadN_sx
def spec_tload(config: Configuration) -> None:
    logger.debug("spec_tload()")

    S = config.store
    instruction = cast(MemoryOp, config.instructions.current)
    memarg = instruction.memarg
    t = instruction.valtype
    # 3
    a = config.frame.module.memory_addrs[0]
    # 5
    mem = S.mems[a]
    # 7
    i = config.pop_operand()
    # 8
    ea = i + memarg.offset
    # 9
    sxflag = instruction.signed
    N = instruction.memory_bit_size.value

    # 10
    if ea + N // 8 > len(mem.data):
        raise Trap("trap")
    # 11
    # TODO: remove type ignore.  replace with formal memory read API.
    bstar = mem.data[ea:ea + N // 8]  # type: ignore
    # 12
    if sxflag:
        n = spec_bytest_inv(t, bstar)
        c = spec_extend_sMN(N, t.bit_size.value, n)
    else:
        c = spec_bytest_inv(t, bstar)
    # 13
    config.push_operand(c)
    logger.debug("loaded %s from memory locations %s to %s", c, ea, ea + N // 8)


def spec_tstore(config: Configuration) -> None:
    logger.debug("spec_tstore()")

    S = config.store
    instruction = cast(MemoryOp, config.instructions.current)
    memarg = instruction.memarg
    t = instruction.valtype
    # 3
    a = config.frame.module.memory_addrs[0]
    # 5
    mem = S.mems[a]
    # 7
    c = config.pop_operand()
    # 9
    i = config.pop_operand()
    # 10
    ea = i + memarg.offset
    # 11
    Nflag = instruction.declared_bit_size is not None
    N = instruction.memory_bit_size.value
    # 12
    if ea + N // 8 > len(mem.data):
        raise Trap("trap")
    # 13
    if Nflag:
        M = t.bit_size.value
        c = spec_wrapMN(M, N, c)
        bstar = spec_bytest(t, c)  # type: ignore
    else:
        bstar = spec_bytest(t, c)  # type: ignore
    # 15
    # TODO: remove type ignore in favor of formal memory writing API
    mem.data[ea:ea + N // 8] = bstar[: N // 8]  # type: ignore
    logger.debug("stored %s to memory locations %s to %s", bstar[:N // 8], ea, ea + N // 8)


def spec_memorysize(config: Configuration) -> None:
    logger.debug("spec_memorysize()")

    S = config.store
    a = config.frame.module.memory_addrs[0]
    mem = S.mems[a]
    sz = UInt32(len(mem.data) // constants.PAGE_SIZE_64K)
    config.push_operand(sz)


def spec_memorygrow(config: Configuration) -> None:
    logger.debug("spec_memorygrow()")

    S = config.store
    a = config.frame.module.memory_addrs[0]
    mem = S.mems[a]
    sz = UInt32(len(mem.data) // constants.PAGE_SIZE_64K)
    n = config.pop_operand()
    try:
        spec_growmem(mem, cast(UInt32, n))
    except ValidationError:
        # put -1 on top of stack
        config.push_operand(constants.INT32_NEGATIVE_ONE)
    else:
        # put the new size on top of the stack
        config.push_operand(sz)


# 4.4.5 CONTROL INSTRUCTIONS


"""
 This implementation deviates from the spec as follows.
   - Three stacks are maintained, operands, control-flow labels, and function-call frames.
     Operand_stack holds only values, control_stack holds only labels. The
     function-call frames are mainted implicitly in Python function calls --
     this will be changed, putting function call frames into the label stack or
     into their own stack.
   - `config` inculdes store S, frame F, instr_list, idx into this instr_list,
     operand_stack, and control_stack.
   - Each label L has extra value for height of operand stack when it started,
     continuation when it is branched to, and end when it's last instruction is
     called.
"""


def spec_nop(config):
    logger.debug("spec_nop()")


def spec_unreachable(config):
    logger.debug("spec_unreachable()")

    raise Trap("trap")


def spec_block(config):
    logger.debug("spec_block()")

    block = cast(Block, config.instructions.current)
    # 1
    # 2
    L = Label(
        arity=len(block.result_type),
        instructions=InstructionSequence(block.instructions),
        is_loop=False,
    )

    # 3
    spec_enter_block(config, L)


def spec_loop(config: Configuration) -> None:
    logger.debug("spec_loop()")

    instruction = cast(Loop, config.instructions.current)
    # 1
    L = Label(
        arity=0,
        instructions=InstructionSequence(instruction.instructions),
        is_loop=True,
    )
    # 2
    spec_enter_block(config, L)


def spec_if(config: Configuration) -> None:
    logger.debug("spec_if()")

    # 2
    c = config.pop_operand()
    # 3
    instruction = cast(If, config.instructions.current)
    result_type = instruction.result_type

    n = len(result_type)
    # 4
    if c:
        L = Label(
            arity=n,
            instructions=InstructionSequence(instruction.instructions),
            is_loop=False,
        )
    else:
        L = Label(
            arity=n,
            instructions=InstructionSequence(instruction.else_instructions),
            is_loop=False,
        )

    spec_enter_block(config, L)


def spec_br(config: Configuration, label_idx: LabelIdx = None) -> None:
    logger.debug('spec_br(%s)', label_idx)

    instruction = cast(Union[Br, BrIf], config.instructions.current)

    if label_idx is None:
        label_idx = instruction.label_idx

    # 2
    L = config.get_by_label_idx(label_idx)
    logger.info('BR: arity: %d', L.arity)
    # 3
    # 5
    # 6
    valn = tuple(config.pop_operand() for _ in range(L.arity))

    if L.is_loop:
        for _ in range(label_idx):
            config.pop_label()
        assert config.active_label is L
        config.instructions.seek(0)
    else:
        for _ in range(label_idx + 1):
            config.pop_label()
    # 7
    for value in valn:
        config.push_operand(value)
    # 8


def spec_br_if(config: Configuration) -> None:
    logger.debug('spec_br_if()')

    instruction = cast(BrIf, config.instructions.current)
    # 2
    c = config.pop_operand()
    # 3
    if c:
        spec_br(config, instruction.label_idx)
    # 4


def spec_br_table(config):
    logger.debug('spec_br_table()')

    instruction = cast(BrTable, config.instructions.current)
    lstar = instruction.label_indices
    lN = instruction.default_idx
    # 2
    i = config.pop_operand()
    # 3
    if i < len(lstar):
        li = lstar[i]
        spec_br(config, li)
    # 4
    else:
        spec_br(config, lN)


def spec_return(config: Configuration) -> None:
    logger.debug('spec_return()')

    # 1
    # 2
    n = config.frame.arity
    # 4
    # 6
    valn = list(reversed([
        config.pop_operand()
        for _ in range(n)
    ]))

    # 8
    config.pop_frame()
    # 9
    for value in valn:
        config.push_operand(value)


def spec_call(config: Configuration) -> None:
    logger.debug('spec_call()')

    instruction = cast(Call, config.instructions.current)
    # 1
    # 3
    addr = config.frame.module.func_addrs[instruction.function_idx]
    # 4
    spec_invoke_function_address(config, addr)


def spec_call_indirect(config: Configuration) -> None:
    logger.debug('spec_call_indirect()')

    S = config.store
    # 1
    # 3
    ta = config.frame.module.table_addrs[0]
    # 5
    tab = S.tables[ta]
    # 7
    instruction = cast(CallIndirect, config.instructions.current)
    ftexpect = config.frame.module.types[instruction.type_idx]
    # 9
    i = int(config.pop_operand())
    # 10
    if len(tab.elem) <= i:
        raise Trap("trap")
    # 11
    if tab.elem[i] is None:
        raise Trap("trap")
    # 12
    addr = tab.elem[i]
    if addr is None:
        raise Exception("Invalid: TODO")
    # 14
    f = S.funcs[addr]
    # 15
    ftactual = f.type
    # 16
    if ftexpect != ftactual:
        raise Trap("trap")
    # 17
    spec_invoke_function_address(config, addr)


# 4.4.6 BLOCKS


def spec_enter_block(config: Configuration, L: Label) -> None:
    logger.debug('spec_enter_block(%s)', L)

    config.push_label(L)


def spec_exit_block(config):
    logger.debug('spec_exit_block(%s)', config.active_label)

    L = config.pop_label()
    for val in L.operand_stack:
        config.push_operand(val)


# 4.4.7 FUNCTION CALLS

def spec_invoke_function_address(config: Configuration,
                                 func_addr: FunctionAddress = None,
                                 ) -> None:
    logger.debug('spec_invoke_function_address(%s)', func_addr)

    S = config.store
    if config.frame_stack_size > 1024:
        # TODO: this is not part of spec, but this is required to pass tests.
        # Tests pass with limit 10000, maybe more
        raise Exhaustion("Function length greater than 1024")

    if func_addr is None:
        if isinstance(config.instructions.current, InvokeInstruction):
            func_addr = config.instructions.current.func_addr
        else:
            raise TypeError(
                "No function address was provided and cannot get address from "
                "instruction."
            )

    # 2
    f = S.funcs[func_addr]
    # 3
    t1n, t2m = f.type
    if isinstance(f, FunctionInstance):
        # 5
        tstar = f.code.locals
        # 6
        instrstarend = f.code.body
        # 8
        valn = list(reversed([
            config.pop_operand()
            for _ in range(len(t1n))
        ]))
        # 9
        val0star: List[TValue] = []
        for valtype in tstar:
            if valtype.is_integer_type:
                val0star.append(UInt32(0))
            elif valtype.is_float_type:
                val0star.append(Float32(0.0))
            else:
                raise Exception(f"Invariant: unkown type '{valtype}'")
        # 10 & 11
        blockinstrstarendend = InstructionSequence(
            cast(
                Tuple[BaseInstruction, ...],
                (Block(t2m, tuple(instrstarend)), End()),
            ),
        )
        F = Frame(
            module=f.module,
            locals=valn + val0star,
            instructions=blockinstrstarendend,
            arity=len(t2m),
        )
        config.push_frame(F)
    elif isinstance(f, HostFunction):
        valn = [config.pop_operand() for _ in range(len(t1n))]
        _, ret = f.hostcode(S, valn)
        if len(ret) > 1:
            raise Exception("Invariant")
        elif ret:
            config.push_operand(ret[0])
    else:
        raise Exception("Invariant: unreachable code path")


def spec_return_from_func(config: Configuration) -> None:
    logger.debug('spec_return_from_func()')

    if config.has_active_label:
        raise Exception("Invariant")

    valn = tuple(config.pop_operand() for _ in range(config.frame.arity))
    config.pop_frame()

    if config.has_active_frame:
        for arg in reversed(valn):
            config.push_operand(arg)
    else:
        for arg in reversed(valn):
            config.result_stack.push(arg)


def spec_end(config: Configuration) -> None:
    logger.debug('spec_end()')

    if config.has_active_label:
        spec_exit_block(config)
    elif config.has_active_frame:
        spec_return_from_func(config)
    else:
        raise Exception("Invariant?")


# 4.4.8 EXPRESSIONS


class InvokeOp:
    text = 'invoke'


class InvokeInstruction(NamedTuple):
    func_addr: FunctionAddress

    @property
    def opcode(self) -> Type[InvokeOp]:
        return InvokeOp


# Map each opcode to the function(s) to invoke when it is encountered. For
# opcodes with two functions, the second function is called by the first
# function.
opcode2exec: Dict[Union[Type[InvokeOp], BinaryOpcode], Tuple[Callable, ...]] = {
    BinaryOpcode.UNREACHABLE: (spec_unreachable,),
    BinaryOpcode.NOP: (spec_nop,),
    BinaryOpcode.BLOCK: (spec_block,),  # blocktype in* end
    BinaryOpcode.LOOP: (spec_loop,),  # blocktype in* end
    BinaryOpcode.IF: (spec_if,),  # blocktype in1* else? in2* end
    BinaryOpcode.ELSE: (spec_end,),  # in2*
    BinaryOpcode.END: (spec_end,),
    BinaryOpcode.BR: (spec_br,),  # labelidx
    BinaryOpcode.BR_IF: (spec_br_if,),  # labelidx
    BinaryOpcode.BR_TABLE: (spec_br_table,),  # labelidx* labelidx
    BinaryOpcode.RETURN: (spec_return,),
    BinaryOpcode.CALL: (spec_call,),  # funcidx
    BinaryOpcode.CALL_INDIRECT: (spec_call_indirect,),  # typeidx 0x00
    BinaryOpcode.DROP: (spec_drop,),
    BinaryOpcode.SELECT: (spec_select,),
    BinaryOpcode.GET_LOCAL: (spec_get_local,),  # localidx
    BinaryOpcode.SET_LOCAL: (spec_set_local,),  # localidx
    BinaryOpcode.TEE_LOCAL: (spec_tee_local,),  # localidx
    BinaryOpcode.GET_GLOBAL: (spec_get_global,),  # globalidx
    BinaryOpcode.SET_GLOBAL: (spec_set_global,),  # globalidx
    BinaryOpcode.I32_LOAD: (spec_tload,),  # memarg
    BinaryOpcode.I64_LOAD: (spec_tload,),  # memarg
    BinaryOpcode.F32_LOAD: (spec_tload,),  # memarg
    BinaryOpcode.F64_LOAD: (spec_tload,),  # memarg
    BinaryOpcode.I32_LOAD8_S: (spec_tload,),  # memarg
    BinaryOpcode.I32_LOAD8_U: (spec_tload,),  # memarg
    BinaryOpcode.I32_LOAD16_S: (spec_tload,),  # memarg
    BinaryOpcode.I32_LOAD16_U: (spec_tload,),  # memarg
    BinaryOpcode.I64_LOAD8_S: (spec_tload,),  # memarg
    BinaryOpcode.I64_LOAD8_U: (spec_tload,),  # memarg
    BinaryOpcode.I64_LOAD16_S: (spec_tload,),  # memarg
    BinaryOpcode.I64_LOAD16_U: (spec_tload,),  # memarg
    BinaryOpcode.I64_LOAD32_S: (spec_tload,),  # memarg
    BinaryOpcode.I64_LOAD32_U: (spec_tload,),  # memarg
    BinaryOpcode.I32_STORE: (spec_tstore,),  # memarg
    BinaryOpcode.I64_STORE: (spec_tstore,),  # memarg
    BinaryOpcode.F32_STORE: (spec_tstore,),  # memarg
    BinaryOpcode.F64_STORE: (spec_tstore,),  # memarg
    BinaryOpcode.I32_STORE8: (spec_tstore,),  # memarg
    BinaryOpcode.I32_STORE16: (spec_tstore,),  # memarg
    BinaryOpcode.I64_STORE8: (spec_tstore,),  # memarg
    BinaryOpcode.I64_STORE16: (spec_tstore,),  # memarg
    BinaryOpcode.I64_STORE32: (spec_tstore,),  # memarg
    BinaryOpcode.MEMORY_SIZE: (spec_memorysize,),
    BinaryOpcode.MEMORY_GROW: (spec_memorygrow,),
    BinaryOpcode.I32_CONST: (spec_tconst,),  # i32
    BinaryOpcode.I64_CONST: (spec_tconst,),  # i64
    BinaryOpcode.F32_CONST: (spec_tconst,),  # f32
    BinaryOpcode.F64_CONST: (spec_tconst,),  # f64
    BinaryOpcode.I32_EQZ: (spec_ttestop, spec_ieqzN),
    BinaryOpcode.I32_EQ: (spec_trelop, spec_ieqN),
    BinaryOpcode.I32_NE: (spec_trelop, spec_ineN),
    BinaryOpcode.I32_LT_S: (spec_trelop, spec_ilt_sN),
    BinaryOpcode.I32_LT_U: (spec_trelop, spec_ilt_uN),
    BinaryOpcode.I32_GT_S: (spec_trelop, spec_igt_sN),
    BinaryOpcode.I32_GT_U: (spec_trelop, spec_igt_uN),
    BinaryOpcode.I32_LE_S: (spec_trelop, spec_ile_sN),
    BinaryOpcode.I32_LE_U: (spec_trelop, spec_ile_uN),
    BinaryOpcode.I32_GE_S: (spec_trelop, spec_ige_sN),
    BinaryOpcode.I32_GE_U: (spec_trelop, spec_ige_uN),
    BinaryOpcode.I64_EQZ: (spec_ttestop, spec_ieqzN),
    BinaryOpcode.I64_EQ: (spec_trelop, spec_ieqN),
    BinaryOpcode.I64_NE: (spec_trelop, spec_ineN),
    BinaryOpcode.I64_LT_S: (spec_trelop, spec_ilt_sN),
    BinaryOpcode.I64_LT_U: (spec_trelop, spec_ilt_uN),
    BinaryOpcode.I64_GT_S: (spec_trelop, spec_igt_sN),
    BinaryOpcode.I64_GT_U: (spec_trelop, spec_igt_uN),
    BinaryOpcode.I64_LE_S: (spec_trelop, spec_ile_sN),
    BinaryOpcode.I64_LE_U: (spec_trelop, spec_ile_uN),
    BinaryOpcode.I64_GE_S: (spec_trelop, spec_ige_sN),
    BinaryOpcode.I64_GE_U: (spec_trelop, spec_ige_uN),
    BinaryOpcode.F32_EQ: (spec_trelop, spec_feqN),
    BinaryOpcode.F32_NE: (spec_trelop, spec_fneN),
    BinaryOpcode.F32_LT: (spec_trelop, spec_fltN),
    BinaryOpcode.F32_GT: (spec_trelop, spec_fgtN),
    BinaryOpcode.F32_LE: (spec_trelop, spec_fleN),
    BinaryOpcode.F32_GE: (spec_trelop, spec_fgeN),
    BinaryOpcode.F64_EQ: (spec_trelop, spec_feqN),
    BinaryOpcode.F64_NE: (spec_trelop, spec_fneN),
    BinaryOpcode.F64_LT: (spec_trelop, spec_fltN),
    BinaryOpcode.F64_GT: (spec_trelop, spec_fgtN),
    BinaryOpcode.F64_LE: (spec_trelop, spec_fleN),
    BinaryOpcode.F64_GE: (spec_trelop, spec_fgeN),
    BinaryOpcode.I32_CLZ: (spec_tunop, spec_iclzN),
    BinaryOpcode.I32_CTZ: (spec_tunop, spec_ictzN),
    BinaryOpcode.I32_POPCNT: (spec_tunop, spec_ipopcntN),
    BinaryOpcode.I32_ADD: (spec_tbinop, spec_iaddN),
    BinaryOpcode.I32_SUB: (spec_tbinop, spec_isubN),
    BinaryOpcode.I32_MUL: (spec_tbinop, spec_imulN),
    BinaryOpcode.I32_DIV_S: (spec_tbinop, spec_idiv_sN),
    BinaryOpcode.I32_DIV_U: (spec_tbinop, spec_idiv_uN),
    BinaryOpcode.I32_REM_S: (spec_tbinop, spec_irem_sN),
    BinaryOpcode.I32_REM_U: (spec_tbinop, spec_irem_uN),
    BinaryOpcode.I32_AND: (spec_tbinop, spec_iandN),
    BinaryOpcode.I32_OR: (spec_tbinop, spec_iorN),
    BinaryOpcode.I32_XOR: (spec_tbinop, spec_ixorN),
    BinaryOpcode.I32_SHL: (spec_tbinop, spec_ishlN),
    BinaryOpcode.I32_SHR_S: (spec_tbinop, spec_ishr_sN),
    BinaryOpcode.I32_SHR_U: (spec_tbinop, spec_ishr_uN),
    BinaryOpcode.I32_ROTL: (spec_tbinop, spec_irotlN),
    BinaryOpcode.I32_ROTR: (spec_tbinop, spec_irotrN),
    BinaryOpcode.I64_CLZ: (spec_tunop, spec_iclzN),
    BinaryOpcode.I64_CTZ: (spec_tunop, spec_ictzN),
    BinaryOpcode.I64_POPCNT: (spec_tunop, spec_ipopcntN),
    BinaryOpcode.I64_ADD: (spec_tbinop, spec_iaddN),
    BinaryOpcode.I64_SUB: (spec_tbinop, spec_isubN),
    BinaryOpcode.I64_MUL: (spec_tbinop, spec_imulN),
    BinaryOpcode.I64_DIV_S: (spec_tbinop, spec_idiv_sN),
    BinaryOpcode.I64_DIV_U: (spec_tbinop, spec_idiv_uN),
    BinaryOpcode.I64_REM_S: (spec_tbinop, spec_irem_sN),
    BinaryOpcode.I64_REM_U: (spec_tbinop, spec_irem_uN),
    BinaryOpcode.I64_AND: (spec_tbinop, spec_iandN),
    BinaryOpcode.I64_OR: (spec_tbinop, spec_iorN),
    BinaryOpcode.I64_XOR: (spec_tbinop, spec_ixorN),
    BinaryOpcode.I64_SHL: (spec_tbinop, spec_ishlN),
    BinaryOpcode.I64_SHR_S: (spec_tbinop, spec_ishr_sN),
    BinaryOpcode.I64_SHR_U: (spec_tbinop, spec_ishr_uN),
    BinaryOpcode.I64_ROTL: (spec_tbinop, spec_irotlN),
    BinaryOpcode.I64_ROTR: (spec_tbinop, spec_irotrN),
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
    # special case
    InvokeOp: (spec_invoke_function_address,),
}


# this executes instr* end. This deviates from the spec.
def spec_expr(config):
    logger.debug('spec_expr()')

    while config.has_active_frame:
        instruction = next(config.instructions)

        logic_fn = opcode2exec[instruction.opcode][0]
        logic_fn(config)

    if len(config.result_stack) > 1:
        raise Exception("Invariant?")
    elif len(config.result_stack) == 1:
        return (config.result_stack.pop(),)
    else:
        return tuple()


#############
# 4.5 MODULES
#############

# 4.5.1 EXTERNAL TYPING

def spec_external_typing(S: Store,
                         extern_desc: TExportAddress,
                         ) -> TExportValue:
    logger.debug('spec_external_typing(%s)', extern_desc)

    if isinstance(extern_desc, FunctionAddress):
        if len(S.funcs) < extern_desc:
            raise Unlinkable("unlinkable")
        funcinst = S.funcs[extern_desc]
        return funcinst.type
    elif isinstance(extern_desc, TableAddress):
        if len(S.tables) < extern_desc:
            raise Unlinkable("unlinkable")
        tableinst = S.tables[extern_desc]
        return TableType(
            limits=Limits(UInt32(len(tableinst.elem)), tableinst.max),
            elem_type=FunctionAddress,
        )
    elif isinstance(extern_desc, MemoryAddress):
        if len(S.mems) < extern_desc:
            raise Unlinkable("unlinkable")
        meminst = S.mems[extern_desc]
        return MemoryType(
            UInt32(len(meminst.data) // constants.PAGE_SIZE_64K),
            meminst.max,
        )
    elif isinstance(extern_desc, GlobalAddress):
        if len(S.globals) < extern_desc:
            raise Unlinkable("unlinkable")
        globalinst = S.globals[extern_desc]
        return GlobalType(
            globalinst.mut,
            globalinst.valtype,
        )
    else:
        raise Unlinkable("unlinkable")


# 4.5.2 IMPORT MATCHING


def spec_externtype_matching_limits(limits_a: Limits, limits_b: Limits) -> str:
    logger.debug('spec_externtype_matching_limits(%s, %s)', limits_a, limits_b)

    if limits_a.min < limits_b.min:
        raise Unlinkable("unlinkable")
    elif limits_b.max is None:
        return "<="
    elif limits_a.max is not None and limits_a.max <= limits_b.max:
        return "<="
    else:
        raise Unlinkable("unlinkable")


def spec_externtype_matching(externtype1, externtype2):
    logger.debug('spec_externtype_matching(%s, %s)', externtype1, externtype2)

    if type(externtype1) is not type(externtype2):
        raise Unlinkable(
            f"Mismatch in extern types: {type(externtype1)} != {type(externtype2)}"
        )
    elif isinstance(externtype1, FunctionType):
        if externtype1 == externtype2:
            return "<="
        else:
            raise Unlinkable(f"Function types not equal: {externtype1} != {externtype2}")
    elif isinstance(externtype1, TableType):
        spec_externtype_matching_limits(externtype1.limits, externtype2.limits)

        if externtype1.elem_type is externtype2.elem_type:
            return "<="
        else:
            raise Unlinkable(
                f"Table element type mismatch: {externtype1.elem_type} != "
                f"{externtype2.elem_type}"
            )
    elif isinstance(externtype1, MemoryType):
        if spec_externtype_matching_limits(externtype1, externtype2) == "<=":
            return "<="
        else:
            # TODO: This code path doesn't appear to be excercised and it
            # likely isn't an invariant.
            raise Exception("Invariant")
    elif isinstance(externtype1, GlobalType):
        if externtype1 == externtype2:
            return "<="
        else:
            raise Unlinkable(f"Globals extern type mismatch: {externtype1} != {externtype2}")
    else:
        raise Unlinkable(f"Unknown extern type: {type(externtype1)}")


# 4.5.3 ALLOCATION


def spec_allocfunc(S: Store,
                   func: Function,
                   module: ModuleInstance,
                   ) -> Tuple[Store, FunctionAddress]:
    logger.debug('spec_allocfunc()')

    funcaddr = FunctionAddress(len(S.funcs))
    function_type = module.types[func.type_idx]
    funcinst = FunctionInstance(function_type, module, func)
    S.funcs.append(funcinst)
    return S, funcaddr


def spec_allochostfunc(S: Store,
                       functype: FunctionType,
                       hostfunc: HostFunctionCallable,
                       ) -> Tuple[Store, FunctionAddress]:
    logger.debug('spec_allochostfunc()')

    funcaddr = FunctionAddress(len(S.funcs))
    funcinst = HostFunction(functype, hostfunc)
    S.funcs.append(funcinst)
    return S, funcaddr


def spec_alloctable(S: Store, table_type: TableType) -> Tuple[Store, TableAddress]:
    logger.debug('spec_alloctable()')

    tableaddr = TableAddress(len(S.tables))
    tableinst = TableInstance(
        elem=[None] * table_type.limits.min,
        max=table_type.limits.max,
    )
    S.tables.append(tableinst)
    return S, tableaddr


def spec_allocmem(S: Store, memory_type: MemoryType) -> Tuple[Store, MemoryAddress]:
    logger.debug('spec_allocmem()')

    memaddr = MemoryAddress(len(S.mems))
    meminst = MemoryInstance(
        data=bytearray(memory_type.min * constants.PAGE_SIZE_64K),
        max=memory_type.max,
    )
    S.mems.append(meminst)
    return S, memaddr


def spec_allocglobal(S: Store,
                     global_type: GlobalType,
                     val: TValue) -> Tuple[Store, GlobalAddress]:
    logger.debug('spec_allocglobal()')

    globaladdr = GlobalAddress(len(S.globals))
    globalinst = GlobalInstance(global_type.valtype, val, global_type.mut)
    S.globals.append(globalinst)
    return S, globaladdr


def spec_growmem(meminst: MemoryInstance, n: UInt32) -> None:
    logger.debug('spec_growmem()')

    if len(meminst.data) % constants.PAGE_SIZE_64K != 0:
        # TODO: runtime validation that should be removed
        raise Exception("Invariant")

    len_ = n + len(meminst.data) // constants.PAGE_SIZE_64K
    if len_ >= constants.UINT16_CEIL:
        raise ValidationError(
            f"Memory length exceeds u16 bounds: {len_} > {constants.UINT16_CEIL}"
        )
    elif meminst.max is not None and meminst.max < len_:
        raise ValidationError(
            f"Memory length exceeds maximum memory size bounds: {len_} > "
            f"{meminst.max}"
        )

    meminst.data.extend(bytearray(
        n * constants.PAGE_SIZE_64K
    ))  # each page created with bytearray(65536) which is 0s


def spec_allocmodule(S: Store,
                     module: Module,
                     externvalimstar: Sequence[TExportAddress],
                     valstar: Tuple[TValue, ...],
                     ) -> Tuple[Store, ModuleInstance]:
    logger.debug('spec_allocmodule()')

    next_function_address = len(S.funcs)

    funcaddrstar = tuple(
        FunctionAddress(addr)
        for addr
        in range(next_function_address, next_function_address + len(module.funcs))
    )
    tableaddrstar = tuple(spec_alloctable(S, table.type)[1] for table in module.tables)
    memaddrstar = tuple(spec_allocmem(S, mem.type)[1] for mem in module.mems)
    globaladdrstar = tuple(
        spec_allocglobal(S, global_.type, valstar[idx])[1]
        for idx, global_ in enumerate(module.globals)
    )

    funcaddrmodstar = spec_funcs_exports(externvalimstar) + funcaddrstar
    tableaddrmodstar = spec_tables_exports(externvalimstar) + tableaddrstar
    memaddrmodstar = spec_memory_exports(externvalimstar) + memaddrstar
    globaladdrmodstar = spec_globals_exports(externvalimstar) + globaladdrstar

    exportinststar: List[ExportInstance] = []
    for exporti in module.exports:
        desc: TExportAddress

        if exporti.is_function:
            desc = funcaddrmodstar[exporti.function_idx]
        elif exporti.is_table:
            desc = tableaddrmodstar[exporti.table_idx]
        elif exporti.is_memory:
            desc = memaddrmodstar[exporti.memory_idx]
        elif exporti.is_global:
            desc = globaladdrmodstar[exporti.global_idx]
        else:
            raise Exception(f"Unknown export: {exporti}")

        exportinststar += [ExportInstance(exporti.name, desc)]

    # TODO: remove type ignores when module instance data structure is
    # formalized
    moduleinst = ModuleInstance(
        types=module.types,
        func_addrs=funcaddrmodstar,
        table_addrs=tableaddrmodstar,
        memory_addrs=memaddrmodstar,
        global_addrs=globaladdrmodstar,
        exports=tuple(exportinststar),
    )

    store_function_addresses = tuple(
        spec_allocfunc(S, func, moduleinst)[1] for func in module.funcs
    )
    if store_function_addresses != funcaddrstar:
        raise Exception(
            "Invariant: actual function addresses don't match expected values:\n"
            f" - store : {store_function_addresses}"
            f" - actual: {funcaddrstar}"
        )

    return S, moduleinst


def spec_instantiate(S, module, externvaln):
    """
    4.5.4
    - https://webassembly.github.io/spec/core/bikeshed/index.html#instantiation%E2%91%A1
    """
    logger.debug('spec_instantiate()')

    # 1
    # 2
    ret = spec_validate_module(module)
    externtypeimn, externtypeexstar = ret
    # 3
    if len(module.imports) != len(externvaln):
        raise Unlinkable("unlinkable")
    # 4
    for i in range(len(externvaln)):
        externtypei = spec_external_typing(S, externvaln[i])
        spec_externtype_matching(externtypei, externtypeimn[i])
    # 5
    valstar = []
    moduleinstim = ModuleInstance(
        types=(),
        func_addrs=(),
        memory_addrs=(),
        table_addrs=(),
        global_addrs=tuple(
            externval
            for externval in externvaln
            if isinstance(externval, GlobalAddress)
        ),
        exports=(),
    )
    # TODO: figure out why previous frame stack had an arity?

    for globali in module.globals:
        F = Frame(
            module=moduleinstim,
            locals=[],
            instructions=InstructionSequence(globali.init),
            arity=1,
        )
        config = Configuration(
            store=S,
        )
        config.push_frame(F)
        ret = spec_expr(config)[0]
        valstar += [ret]

    # 6
    S, moduleinst = spec_allocmodule(S, module, externvaln, valstar)
    # 7
    # 8
    # 9
    tableinst = []
    eo = []
    for elemi in module.elem:
        F = Frame(
            module=moduleinst,
            locals=[],
            instructions=InstructionSequence(elemi.offset),
            arity=1,
        )
        config = Configuration(store=S)
        config.push_frame(F)
        eovali = spec_expr(config)[0]
        eoi = eovali
        eo += [eoi]
        tableidxi = elemi.table_idx
        tableaddri = moduleinst.table_addrs[tableidxi]
        tableinsti = S.tables[tableaddri]
        tableinst += [tableinsti]
        eendi = eoi + len(elemi.init)
        if eendi > len(tableinsti.elem):
            raise Unlinkable("unlinkable")
    # 10
    meminst = []
    do = []
    for datai in module.data:
        F = Frame(
            module=moduleinst,
            locals=[],
            instructions=InstructionSequence(datai.offset),
            arity=1,
        )
        config = Configuration(store=S)
        config.push_frame(F)
        dovali = spec_expr(config)
        doi = dovali[0]
        do += [doi]
        memidxi = datai.mem_idx
        memaddri = moduleinst.memory_addrs[memidxi]
        meminsti = S.mems[memaddri]
        meminst += [meminsti]
        dendi = doi + len(datai.init)
        if dendi > len(meminsti.data):
            raise Unlinkable("unlinkable")
    # 11
    # 12
    # 13
    for i, elemi in enumerate(module.elem):
        for j, funcidxij in enumerate(elemi.init):
            funcaddrij = moduleinst.func_addrs[funcidxij]
            tableinst[i].elem[eo[i] + j] = funcaddrij
    # 14
    for i, datai in enumerate(module.data):
        for j, bij in enumerate(datai.init):
            meminst[i].data[do[i] + j] = bij
    # 15
    if module.start is not None:
        funcaddr = moduleinst.func_addrs[module.start.function_idx]
        ret = spec_invoke(S, funcaddr, [])
    else:
        ret = None

    return S, moduleinst, ret


# 4.5.5 INVOCATION

# valn looks like [["i32.const",3],["i32.const",199], ...]
def spec_invoke(S: Store,
                funcaddr: FunctionAddress,
                valn: Tuple[Tuple[ValType, TValue], ...],
                ) -> Tuple[TValue, ...]:
    logger.debug('spec_invoke()')

    # 1
    if len(S.funcs) < funcaddr or funcaddr < 0:
        raise Exception("bad address")
    # 2
    funcinst = S.funcs[funcaddr]
    # 5
    t1n, t2m = funcinst.type
    # 4
    if len(valn) != len(t1n):
        raise Exception("wrong number of arguments")
    # 5
    for ti, (valt, val) in zip(t1n, valn):
        if ti is not valt:
            raise Exception("argument type mismatch")

    # 6
    # 7
    if isinstance(funcinst, FunctionInstance):
        F = Frame(
            module=ModuleInstance((), (), (), (), (), ()),
            locals=[],
            instructions=InstructionSequence(cast(
                Tuple[BaseInstruction, ...],
                (InvokeInstruction(funcaddr), End()),
            )),
            arity=len(t2m),
        )
        config = Configuration(store=S)
        config.push_frame(F)
        for _, arg in valn:
            config.push_operand(arg)

        valresm = spec_expr(config)
        assert valresm is not None
        return valresm
    elif isinstance(funcinst, HostFunction):
        operand_stack = OperandStack()
        for _, arg in valn:
            operand_stack.push(arg)
        S, valresm = funcinst.hostcode(S, operand_stack)
        assert valresm is not None
        return valresm
    else:
        raise Exception(f"Invariant: unknown function type: {type(funcinst)}")


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


def init_store():
    return Store([], [], [], [])


# 7.1.2 MODULES


def decode_module(bytestar):
    stream = io.BytesIO(bytestar)
    try:
        return parse_module(stream)
    except ParseError as err:
        raise MalformedModule from err


def validate_module(module):
    try:
        spec_validate_module(module)
    except ValidationError as err:
        raise InvalidModule from err


# TODO: tighten type hint for `externvalstar`
def instantiate_module(store: Store,
                       module: Module,
                       externvalstar: Tuple[Any, ...],
                       ) -> Tuple[Store, ModuleInstance, TValue]:
    # TODO: handle spec deviation if necessary
    # we deviate from the spec by also returning the return value
    ret = spec_instantiate(store, module, externvalstar)

    store, modinst, startret = ret
    return store, modinst, startret


# 7.1.3 EXPORTS


# 7.1.4 FUNCTIONS


def alloc_func(store, functype, hostfunc):
    store, funcaddr = spec_allochostfunc(store, functype, hostfunc)
    return store, funcaddr


def invoke_func(store, funcaddr, valstar):
    ret = spec_invoke(store, funcaddr, valstar)
    return store, ret


# 7.1.4 TABLES


def alloc_table(store, tabletype):
    store, tableaddr = spec_alloctable(store, tabletype)
    return store, tableaddr


# 7.1.6 MEMORIES


def alloc_mem(store, memtype):
    store, memaddr = spec_allocmem(store, memtype)
    return store, memaddr


# 7.1.7 GLOBALS


def alloc_global(store, globaltype, val):
    return spec_allocglobal(store, globaltype, val)
