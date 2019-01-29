import io
import itertools
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
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)
import uuid

from wasm import (
    constants,
)
from wasm._utils.validation import (
    get_duplicates,
)
from wasm.datatypes import (
    BitSize,
    Configuration,
    DataSegment,
    ElementSegment,
    Export,
    ExportInstance,
    Frame,
    FrameStack,
    FuncIdx,
    Function,
    FunctionAddress,
    FunctionInstance,
    FunctionType,
    Global,
    GlobalAddress,
    GlobalIdx,
    GlobalInstance,
    GlobalType,
    HostFunction,
    Import,
    InstructionSequence,
    Label,
    LabelIdx,
    LabelStack,
    Limits,
    Memory,
    MemoryAddress,
    MemoryIdx,
    MemoryInstance,
    MemoryType,
    Module,
    ModuleInstance,
    Mutability,
    StartFunction,
    Table,
    TableAddress,
    TableIdx,
    TableInstance,
    TableType,
    TypeIdx,
    ValType,
    ValueStack,
)
from wasm.exceptions import (
    Exhaustion,
    InvalidModule,
    MalformedModule,
    Trap,
    Unlinkable,
    ValidationError,
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
    F32Const,
    F64Const,
    GlobalOp,
    I32Const,
    I64Const,
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
from wasm.instructions.variable import (
    GlobalAction,
)
from wasm.opcodes import (
    BinaryOpcode,
)
from wasm.parsers.instructions import (
    parse_instruction,
)
from wasm.typing import (
    Float32,
    HostFunctionCallable,
    Store,
    TValue,
    UInt8,
    UInt32,
)
from wasm.validation import (
    Context,
)

logger = logging.getLogger('wasm.spec')


###############
###############
# 2 STRUCTURE #
###############
###############

# Chapter 2 defines the abstract syntax, which is used throughout the implementation. Not much is needed from this section, since most abstrct syntax is nested lists and dictionaries

# 2.2.3 FLOATING-POINT

# functions in this sectio are not currently used since we decided to use native Python floats, and struct.pack()/unpack() to encode/decode, but we may use these later to pass the rest of the NaN tests


def spec_fN(N, f):
    fNmag = spec_fNmag(N, f)
    if f >= 0:
        return fNmag
    else:
        return -1 * fNmag


def spec_signif(N):
    logging.debug("spec_signif(%s)", N)

    if N == 32:
        return 23
    elif N == 64:
        return 52
    else:
        raise Exception(f"Invariant: got '{N}' | expected one of 32/64")


def spec_signif_inv(signif):
    logging.debug("spec_signif_inv(%s)", N)

    if signif == 23:
        return 32
    elif signif == 52:
        return 64
    else:
        raise Exception(f"Invariant: got '{N}' | expected one of 32/64")


def spec_expon(N):
    logging.debug("spec_expon(%s)", N)

    if N == 32:
        return 8
    elif N == 64:
        return 11
    else:
        raise Exception(f"Invariant: got '{N}' | expected one of 32/64")


def spec_expon_inv(expon):
    logging.debug("spec_expon_inv(%s)", expon)

    if expon == 8:
        return 32
    elif expon == 11:
        return 64
    else:
        raise Exception(f"Invariant: got '{expon}' | expected one of 8/11")


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


def spec_validate_limit(limits: Limits, upper_bound: int) -> None:
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#limits%E2%91%A2
    """
    if limits.min > constants.UINT32_MAX:
        raise InvalidModule("Limits.min is outside of u32 range: Got {limits.min}")
    elif limits.min > upper_bound:
        raise InvalidModule(f"Limits.min exceeds upper bound: {limits.min} > {upper_bound}")
    elif limits.max is not None:
        if limits.max > constants.UINT32_MAX:
            raise InvalidModule("Limits.max is outside of u32 range: Got {limits.max}")
        elif limits.max > upper_bound:
            raise InvalidModule(f"Limits.max exceeds upper bound: {limits.max} > {upper_bound}")
        elif limits.max < limits.min:
            raise InvalidModule(
                f"Limits.max cannot be greater than Limits.min: {limits.max} > "
                f"{limits.min}"
            )


# 3.2.2 FUNCTION TYPES


def spec_validate_functype(ft: FunctionType) -> None:
    if len(ft.results) > 1:
        raise InvalidModule(
            f"Function types may only have one result.  Got {len(ft.results)}"
        )


# 3.2.3 TABLE TYPES


def spec_validate_tabletype(table_type: TableType) -> TableType:
    spec_validate_limit(table_type.limits, constants.UINT32_CEIL)
    return table_type


# 3.2.4 MEMORY TYPES


def spec_validate_memtype(memory_type: MemoryType) -> MemoryType:
    limits = Limits(memory_type.min, memory_type.max)
    spec_validate_limit(limits, constants.UINT16_CEIL)
    return memory_type


# 3.2.5 GLOBAL TYPES


def spec_validate_globaltype(global_type: GlobalType) -> GlobalType:
    return global_type


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


def spec_validate_expr(context: Context, expr: Expression) -> Tuple[ValType, ...]:
    opd_stack: List[ValType] = []
    ctrl_stack: List[Dict[Any, Any]] = []

    iterate_through_expression_and_validate_each_opcode(
        expr, context, opd_stack, ctrl_stack
    )  # call to the algorithm in the appendix

    if len(opd_stack) > 1:
        raise InvalidModule("invalid")
    else:
        return tuple(opd_stack)


def spec_validate_const_instr(context: Context, instruction: BaseInstruction) -> Mutability:
    if isinstance(instruction, GlobalOp):
        if instruction.action is not GlobalAction.get:
            raise InvalidModule(f"Must be a get_local instruction.  Got {instruction}")

        global_ = context.get_global(instruction.global_idx)

        if global_.mut is not Mutability.const:
            raise InvalidModule(f"Retrieved global type is mutable")
    elif not isinstance(instruction, (I32Const, I64Const, F32Const, F64Const, GlobalOp)):
        raise InvalidModule(
            f"Instruction is not a const: Got {instruction}"
        )

    return Mutability.const


def spec_validate_const_expr(context: Context, expr: Expression) -> Mutability:
    # expr is in AST form
    for e in expr[:-1]:
        spec_validate_const_instr(context, e)

    if not isinstance(expr[-1], End):
        raise InvalidModule(
            f"Expression must terminate with an `End` instruction: Got {expr[-1]}"
        )

    return Mutability.const


#############
# 3.4 MODULES
#############

# 3.4.1 FUNCTIONS


def spec_validate_func(context: Context, func: Function) -> Tuple[ValType, ...]:
    if func.type >= len(context.types):
        raise InvalidModule(
            f"Function type index out of range: {func.type} >= {len(context.types)}"
        )

    func_type: FunctionType = context.types[func.type]

    t1 = func_type.params
    t2 = func_type.results
    func_context = context.prime(
        locals=tuple(t1 + func.locals),
        labels=t2,
        returns=t2,
    )
    # validate body using algorithm in appendix
    # TODO: resolve this comment:
    # - "spec didn't nest func body in a block, but algorithm in appendix gives errors otherwise"
    instrstar = cast(Tuple[BaseInstruction, ...], (
        Block(
            t2,
            func.body,
        ),
    ))
    ft = spec_validate_expr(func_context, instrstar)

    return ft


# 3.4.2 TABLES


def spec_validate_table(table):
    return spec_validate_tabletype(table.type)


# 3.4.3 MEMORIES


def spec_validate_mem(memory):
    ret = spec_validate_memtype(memory.type)

    return ret


# 3.4.4 GLOBALS


def spec_validate_global(C, global_):
    spec_validate_globaltype(global_.type)
    # validate expr, but wrap it in a block first since empty control stack gives errors
    # but first wrap in block with appropriate return type
    instrstar = (
        Block(
            (global_.type.valtype,),
            global_.init,
        ),
    )
    ret = spec_validate_expr(C, instrstar)
    if ret != (global_.type.valtype,):
        raise InvalidModule("invalid")
    ret = spec_validate_const_expr(C, global_.init)
    return global_.type


# 3.4.5 ELEMENT SEGMENT


def spec_validate_elem(context: Context, element_segment: ElementSegment) -> None:
    context.validate_table_idx(element_segment.table_idx)
    table_type = context.get_table(element_segment.table_idx)

    limits = table_type.limits
    elem_type = table_type.elem_type
    if elem_type is not FunctionAddress:
        raise InvalidModule("invalid")
    # first wrap in block with appropriate return type
    instrstar = cast(Tuple[BaseInstruction, ...], (
        Block(
            (ValType.i32,),
            element_segment.offset,
        ),
    ))
    ret = spec_validate_expr(context, instrstar)
    if ret != (ValType.i32,):
        raise InvalidModule("invalid")
    spec_validate_const_expr(context, element_segment.offset)
    for y in element_segment.init:
        context.validate_func_idx(y)


# 3.4.6 DATA SEGMENTS


def spec_validate_data(context: Context, data_segment: DataSegment) -> None:
    context.validate_mem_idx(data_segment.mem_idx)

    instrstar = cast(Tuple[BaseInstruction, ...], (
        Block(
            (ValType.i32,),
            data_segment.offset,
        ),
    ))
    ret = spec_validate_expr(context, instrstar)
    if tuple(ret) != (ValType.i32,):
        raise InvalidModule(
            f"Invalid data segment.  Return type must be '(i32,)'.  Got {ret}"
        )
    spec_validate_const_expr(context, data_segment.offset)


# 3.4.7 START FUNCTION


def spec_validate_start(context: Context, start: StartFunction) -> None:
    context.validate_func_idx(start.func_idx)
    func_type = context.get_func(start.func_idx)

    if func_type != FunctionType((), ()):
        raise InvalidModule(
            "Start function may not have arguments or a result type.  Got "
            f"{func_type}"
        )


# 3.4.8 EXPORTS


TExportValue = Union[FunctionType, TableType, MemoryType, GlobalType]
TExportDesc = Union[FuncIdx, GlobalIdx, MemoryIdx, TableIdx]


def spec_validate_export(context: Context, export: Export) -> TExportValue:
    return spec_validate_exportdesc(context, export.desc)


def spec_validate_exportdesc(context: Context,
                             idx: TExportDesc) -> TExportValue:
    if isinstance(idx, FuncIdx):
        context.validate_func_idx(idx)
        return context.get_func(idx)
    elif isinstance(idx, TableIdx):
        context.validate_table_idx(idx)
        return context.get_table(idx)
    elif isinstance(idx, MemoryIdx):
        context.validate_mem_idx(idx)
        return context.get_mem(idx)
    elif isinstance(idx, GlobalIdx):
        context.validate_global_idx(idx)
        global_ = context.get_global(idx)
        # TODO: tests fail linking.wast: $Mg exports a mutable global, seems not to parse in wabt
        # if global_.mut is not Mutability.const:
        #     raise InvalidModule("Globals must be constant")
        return global_
    else:
        raise InvalidModule(f"Unknown export descripto type: {type(idx)}")


# 3.4.9 IMPORTS


TImport = Union[FunctionType, TableType, MemoryType, GlobalType]


# TODO: the return type of this function should probably be changed.
def spec_validate_import(context: Context, import_: Import) -> TImport:
    return spec_validate_importdesc(context, import_.desc)


TImportDesc = Union[TypeIdx, GlobalType, MemoryType, TableType]


def spec_validate_importdesc(context: Context, descriptor: TImportDesc) -> TImport:
    if isinstance(descriptor, TypeIdx):
        context.validate_type_idx(descriptor)
        return context.get_type(descriptor)
    elif isinstance(descriptor, TableType):
        spec_validate_tabletype(descriptor)
        return descriptor
    elif isinstance(descriptor, MemoryType):
        spec_validate_memtype(descriptor)
        return descriptor
    elif isinstance(descriptor, GlobalType):
        spec_validate_globaltype(descriptor)
        # TODO: confirm compliance with spec.  This comment indicates a
        # validation step being ignore that causes a spec test to fail when
        # enabled.
        # if global_type[0] != "const": raise InvalidModule("invalid") #TODO: this was in the spec, but tests fail linking.wast: $Mg exports a mutable global, seems not to parse in wabt
        return descriptor
    else:
        raise InvalidModule("invalid")


# 3.4.10 MODULE


def spec_validate_module(module: Module) -> List[List[ExternType]]:
    # mod is the module to validate
    ftstar: List[FunctionType] = []

    for func in module.funcs:
        if len(module.types) <= func.type:
            # this was not explicit in spec, how about other *tstar
            raise InvalidModule("invalid")
        ftstar += [module.types[func.type]]

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
        funcs=iftstar + tuple(ftstar),
        tables=ittstar + ttstar,
        mems=imtstar + mtstar,
        globals=igtstar + gtstar,
        locals=(),
        labels=(),
        returns=(),

    )
    context_p = Context(
        types=(),
        funcs=(),
        tables=(),
        mems=(),
        globals=tuple(igtstar),
        locals=(),
        labels=(),
        returns=(),
    )

    # et* is needed later, here is a good place to do it
    etstar: List[ExternType] = []
    for export in module.exports:
        if export.is_function:
            if len(context.funcs) <= export.desc:
                # this was not explicit in spec
                raise InvalidModule("invalid")
            etstar.append(context.funcs[export.desc])
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
        spec_validate_functype(functypei)

    for i, func in enumerate(module.funcs):
        ft = spec_validate_func(context, func)
        if ft != ftstar[i].results:
            raise InvalidModule("invalid")

    for i, table in enumerate(module.tables):
        tt = spec_validate_table(table)
        if tt != ttstar[i]:
            raise InvalidModule("invalid")

    for i, mem in enumerate(module.mems):
        mt = spec_validate_mem(mem)
        if mt != mtstar[i]:
            raise InvalidModule("invalid")

    for i, global_ in enumerate(module.globals):
        # TODO: this is the only place that `context_p` is used and can
        # probably be cleaned up to not polute local namespace.
        gt = spec_validate_global(context_p, global_)
        if gt != gtstar[i]:
            raise InvalidModule("invalid")

    for elem in module.elem:
        spec_validate_elem(context, elem)

    for data in module.data:
        spec_validate_data(context, data)

    if module.start is not None:
        spec_validate_start(context, module.start)

    for i, import_ in enumerate(module.imports):
        it = spec_validate_import(context, import_)
        if it != itstar[i]:
            raise InvalidModule("invalid")

    for i, export in enumerate(module.exports):
        et = spec_validate_export(context, export)
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


# TODO: accurate type for `c`
def spec_bitst(valtype: ValType, c: Any) -> str:
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
        bytes_ += bytearray([int(bits[8 * i : 8 * (i + 1)], 2)])
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


def spec_bytesiN(N, i):
    logger.debug("spec_bytesiN(%s, %s)", N, i)

    bits = spec_bitsiN(N, i)
    # convert bits to bytes
    bytes_ = bytearray()
    for byteIdx in range(0, len(bits), 8):
        bytes_ += bytearray([int(bits[byteIdx : byteIdx + 8], 2)])
    return bytes_


def spec_bytesiN_inv(N, bytes_):
    logger.debug("spec_bytesiN_inv(%s, %s)", N, bytes_)

    bits = ""
    for byte in bytes_:
        bits += spec_ibitsN(8, byte)
    return spec_ibitsN_inv(N, bits)


# TODO: these are unused, but might use when refactor floats to pass NaN significand tests
def spec_bytesfN(N: int, z: float) -> bytes:
    logger.debug("spec_bytesfN(%s, %s)", N, z)

    if N == 32:
        z_bytes = struct.pack(">f", z)
    elif N == 64:
        z_bytes = struct.pack(">d", z)
    else:
        raise Exception(f"Invariant: bit size must be one of 32/64 - Got '{N}'")

    return z_bytes


def spec_bytesfN_inv(N, bytes_):
    logger.debug("spec_bytesfN_inv(%s, %s)", N, bytes_)

    if N == 32:
        z = struct.unpack(">f", bytes_)[0]
    elif N == 64:
        z = struct.unpack(">d", bytes_)[0]
    else:
        raise Exception(f"Invariant: bit size must be one of 32/64 - Got '{N}'")

    return z


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
    d1Nmkm1 = d0d1Nmkm1d2k[1 : N - k]
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
    d2k = d1Nmkd2k[N - k :]
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

    config.value_stack.push(value)


def spec_tunop(config: Configuration) -> None:
    logger.debug("spec_tunop()")

    instruction = cast(BinOp, config.instructions.current)
    t = instruction.valtype
    op = opcode2exec[instruction.opcode][1]
    c1 = config.value_stack.pop()
    c = op(t.bit_size.value, c1)

    config.value_stack.push(c)


def spec_tbinop(config: Configuration) -> None:
    logger.debug("spec_tbinop()")

    instruction = cast(BinOp, config.instructions.current)
    t = instruction.valtype
    op = opcode2exec[instruction.opcode][1]
    c2, c1 = config.value_stack.pop2()
    c = op(t.bit_size.value, c1, c2)

    config.value_stack.push(c)


def spec_ttestop(config: Configuration) -> None:
    logger.debug("spec_ttestop()")

    instruction = cast(TestOp, config.instructions.current)
    t = instruction.valtype
    op = opcode2exec[instruction.opcode][1]
    c1 = config.value_stack.pop()
    c = op(t.bit_size.value, c1)

    config.value_stack.push(c)


def spec_trelop(config: Configuration) -> None:
    logger.debug("spec_trelop()")

    instruction = cast(RelOp, config.instructions.current)
    t = instruction.valtype
    op = opcode2exec[instruction.opcode][1]
    c2, c1 = config.value_stack.pop2()
    c = op(t.bit_size.value, c1, c2)

    config.value_stack.push(c)


T_t2cvt = Union[Wrap, Truncate, Extend, Demote, Promote, Convert, Reinterpret]


def spec_t2cvtopt1(config: Configuration) -> None:
    logger.debug("spec_t2cvtopt1()")

    instruction = cast(T_t2cvt, config.instructions.current)
    t2 = instruction.valtype
    t1 = instruction.result
    op = opcode2exec[instruction.opcode][1]
    c1 = config.value_stack.pop()

    if instruction.opcode.is_reinterpret:
        c2 = op(t1, t2, c1)
    else:
        c2 = op(t1.bit_size.value, t2.bit_size.value, c1)

    config.value_stack.push(c2)


# 4.4.2 PARAMETRIC INSTRUCTIONS


def spec_drop(config: Configuration) -> None:
    logger.debug("spec_drop()")

    config.value_stack.pop()


def spec_select(config: Configuration) -> None:
    logger.debug("spec_select()")

    c, val1, val2 = config.value_stack.pop3()

    if c:
        config.value_stack.push(val2)
    else:
        config.value_stack.push(val1)


# 4.4.3 VARIABLE INSTRUCTIONS


def spec_get_local(config: Configuration) -> None:
    logger.debug("spec_get_local()")

    instruction = cast(LocalOp, config.instructions.current)
    val = config.frame.locals[instruction.local_idx]
    config.value_stack.push(val)


def spec_set_local(config: Configuration) -> None:
    logger.debug("spec_set_local()")

    instruction = cast(LocalOp, config.instructions.current)
    val = config.value_stack.pop()
    config.frame.locals[instruction.local_idx] = val


def spec_tee_local(config: Configuration) -> None:
    logger.debug("spec_tee_local()")

    val = config.value_stack.pop()
    config.value_stack.push(val)
    config.value_stack.push(val)
    spec_set_local(config)


def spec_get_global(config: Configuration) -> None:
    logger.debug("spec_get_global()")

    S = config.store
    instruction = cast(GlobalOp, config.instructions.current)
    a = config.frame.module.global_addrs[instruction.global_idx]
    glob = S["globals"][a]
    config.value_stack.push(glob.value)


def spec_set_global(config):
    logger.debug("spec_set_global()")

    S = config.store
    instruction = cast(GlobalOp, config.instructions.current)
    a = config.frame.module.global_addrs[instruction.global_idx]
    glob = S["globals"][a]
    if glob.mut is not Mutability.var:
        raise Exception("Attempt to set immutable global")
    val = config.value_stack.pop()
    S["globals"][a] = GlobalInstance(glob.valtype, val, glob.mut)


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
    mem = S["mems"][a]
    # 7
    i = config.value_stack.pop()
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
    bstar = mem.data[ea : ea + N // 8]  # type: ignore
    # 12
    if sxflag:
        n = spec_bytest_inv(t, bstar)
        c = spec_extend_sMN(N, t.bit_size.value, n)
    else:
        c = spec_bytest_inv(t, bstar)
    # 13
    config.value_stack.push(c)
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
    mem = S["mems"][a]
    # 7
    c = config.value_stack.pop()
    # 9
    i = config.value_stack.pop()
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
    mem.data[ea : ea + N // 8] = bstar[: N // 8]  # type: ignore
    logger.debug("stored %s to memory locations %s to %s", bstar[:N//8], ea, ea + N // 8)


def spec_memorysize(config: Configuration) -> None:
    logger.debug("spec_memorysize()")

    S = config.store
    a = config.frame.module.memory_addrs[0]
    mem = S["mems"][a]
    sz = UInt32(len(mem.data) // constants.PAGE_SIZE_64K)
    config.value_stack.push(sz)


def spec_memorygrow(config: Configuration) -> None:
    logger.debug("spec_memorygrow()")

    S = config.store
    a = config.frame.module.memory_addrs[0]
    mem = S["mems"][a]
    sz = UInt32(len(mem.data) // constants.PAGE_SIZE_64K)
    n = config.value_stack.pop()
    spec_growmem(mem, n)  # type: ignore
    if sz + n == len(mem.data) // constants.PAGE_SIZE_64K:  # success
        config.value_stack.push(sz)
    else:
        # TODO: this potentially ends up leaving the memory in an invalid state
        # because it was *grown* above.
        config.value_stack.push(constants.INT32_NEGATIVE_ONE)  # put -1 on top of stack


# 4.4.5 CONTROL INSTRUCTIONS


"""
 This implementation deviates from the spec as follows.
   - Three stacks are maintained, operands, control-flow labels, and function-call frames.
     Operand_stack holds only values, control_stack holds only labels. The function-call frames are mainted implicitly in Python function calls -- this will be changed, putting function call frames into the label stack or into their own stack.
   - `config` inculdes store S, frame F, instr_list, idx into this instr_list, operand_stack, and control_stack.
   - Each label L has extra value for height of operand stack when it started, continuation when it is branched to, and end when it's last instruction is called.
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
        height=len(config.value_stack),
        instructions=InstructionSequence(block.instructions),
        is_loop=False,
        frame_id=config.frame.id,
    )

    # 3
    spec_enter_block(config, L)


def spec_loop(config: Configuration) -> None:
    logger.debug("spec_loop()")

    instruction = cast(Loop, config.instructions.current)
    # 1
    L = Label(
        arity=0,
        height=len(config.value_stack),
        instructions=InstructionSequence(instruction.instructions),
        is_loop=True,
        frame_id=config.frame.id,
    )
    # 2
    spec_enter_block(config, L)


def spec_if(config: Configuration) -> None:
    logger.debug("spec_if()")

    # 2
    c = config.value_stack.pop()
    logger.debug('IF: %s', c)
    # 3
    instruction = cast(If, config.instructions.current)
    result_type = instruction.result_type

    n = len(result_type)
    # 4
    if c:
        L = Label(
            arity=n,
            height=len(config.value_stack),
            instructions=InstructionSequence(instruction.instructions),
            is_loop=False,
            frame_id=config.frame.id,
        )
    else:
        L = Label(
            arity=n,
            height=len(config.value_stack),
            instructions=InstructionSequence(instruction.else_instructions),
            is_loop=False,
            frame_id=config.frame.id,
        )

    spec_enter_block(config, L)


def spec_br(config: Configuration, label_idx: LabelIdx=None) -> None:
    logger.debug('spec_br(%s)', label_idx)

    instruction = cast(Union[Br, BrIf], config.instructions.current)

    if label_idx is None:
        label_idx = instruction.label_idx

    # 2
    L = config.label_stack.get_by_label_idx(label_idx)
    # 3
    # 5
    # 6
    valn = [config.value_stack.pop() for _ in range(L.arity)]
    while len(config.value_stack) > L.height:
        config.value_stack.pop()

    if L.is_loop:
        for _ in range(label_idx):
            config.label_stack.pop()
        # TODO: remove runtime check
        assert config.label is L
        config.instructions.seek(0)
    else:
        for _ in range(label_idx + 1):
            config.label_stack.pop()
    # 7
    for value in valn:
        config.value_stack.push(value)
    # 8


def spec_br_if(config: Configuration) -> None:
    logger.debug('spec_br_if()')

    instruction = cast(BrIf, config.instructions.current)
    # 2
    c = config.value_stack.pop()
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
    i = config.value_stack.pop()
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
        config.value_stack.pop()
        for _ in range(n)
    ]))
    while len(config.value_stack) > config.frame.height:
        logger.info('POPPING')
        config.value_stack.pop()
    # 8
    config.frame_stack.pop()
    # 9
    for value in valn:
        config.value_stack.push(value)


def spec_call(config: Configuration) -> None:
    logger.debug('spec_call()')

    instruction = cast(Call, config.instructions.current)
    # 1
    # 3
    addr = config.frame.module.func_addrs[instruction.func_idx]
    # 4
    spec_invoke_function_address(config, addr)


def spec_call_indirect(config: Configuration) -> None:
    logger.debug('spec_call_indirect()')

    S = config.store
    # 1
    # 3
    ta = config.frame.module.table_addrs[0]
    # 5
    tab = S["tables"][ta]
    # 7
    instruction = cast(CallIndirect, config.instructions.current)
    ftexpect = config.frame.module.types[instruction.type_idx]
    # 9
    i = config.value_stack.pop()
    # 10
    if len(tab.elem) <= i:
        raise Trap("trap")
    # 11
    if tab.elem[i] is None:
        raise Trap("trap")
    # 12
    addr = tab.elem[i]
    # 14
    f = S["funcs"][addr]
    # 15
    ftactual = f.type
    # 16
    if ftexpect != ftactual:
        raise Trap("trap")
    # 17
    spec_invoke_function_address(config, addr)


# 4.4.6 BLOCKS


def spec_enter_block(config: Configuration, L: Label) -> None:
    logger.debug('spec_enter_block()')

    # 1
    # 2
    config.label_stack.push(L)


def spec_exit_block(config):
    logger.debug('spec_exit_block()')

    # 4
    # 6
    config.label_stack.pop()


# 4.4.7 FUNCTION CALLS

def spec_invoke_function_address(config: Configuration,
                                 func_addr: FunctionAddress = None,
                                 ) -> None:
    logger.debug('spec_invoke_function_address(%s)', func_addr)

    S = config.store
    if len(config.frame_stack) > 1024:
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
    f = S["funcs"][func_addr]
    # 3
    t1n, t2m = f.type
    if isinstance(f, FunctionInstance):
        # 5
        tstar = f.code.locals
        # 6
        instrstarend = f.code.body
        # 8
        valn = list(reversed([
            config.value_stack.pop()
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
            id=uuid.uuid4(),
            module=f.module,
            locals=valn + val0star,
            instructions=blockinstrstarendend,
            arity=len(t2m),
            height=len(config.value_stack),
        )
        config.frame_stack.push(F)
    elif isinstance(f, HostFunction):
        valn = [config.value_stack.pop() for _ in range(len(t1n))]
        _, ret = f.hostcode(S, valn)
        if len(ret) > 1:
            raise Exception("Invariant")
        elif ret:
            config.value_stack.push(ret[0])
    else:
        raise Exception("Invariant: unreachable code path")


# this is unused for now
# this is called when end of function reached without return or trap aborting it
def spec_return_from_func(config: Configuration) -> None:
    # TODO: this is no longer used
    logger.debug('spec_return_from_func()')

    # 1
    # 2,3,4,7 not needed since we have separate operand stack
    # 6
    config.frame_stack.pop()
    # 8


def spec_end(config: Configuration) -> None:
    logger.debug('spec_end()')

    if config.has_active_label:
        logger.debug('popping label stack')
        spec_exit_block(config)
    elif len(config.frame_stack) >= 1:
        logger.debug('popping frame stack')
        # continuation for case of init elem or data or global
        config.frame_stack.pop()
    else:
        raise Exception("Invariant?")


# 4.4.8 EXPRESSIONS


class InvokeOp:
    text = 'invoke'


class InvokeInstruction(NamedTuple):
    func_addr: FuncIdx

    @property
    def opcode(self) -> Type[InvokeOp]:
        return InvokeOp


# Map each opcode to the function(s) to invoke when it is encountered. For opcodes with two functions, the second function is called by the first function.
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


# this is the main loop over instr* end
# this is not in the spec
def instrstarend_loop(config):
    logger.debug('instrstarend_loop()')

    # TODO: try to refactor to make this loop have a defined exit condition.
    while True:
        # idx<len(instrs) since instrstar[-1]=="end" which changes instrstar
        instruction = config["instrstar"][config["idx"]]
        ret = opcode2exec[instruction.opcode][0](config)
        if ret:
            return ret, config["operand_stack"]  # eg "done"


# this executes instr* end. This deviates from the spec.
def spec_expr(config):
    logger.debug('spec_expr()')


    while config.is_executable:
        try:
            instruction = next(config.instructions)
        except StopIteration:
            break
        #logger.debug('INSTRUCTION: %s', instruction.opcode.text)
        #logger.debug('LOCALS: %s', config.frame.locals)
        #logger.debug('NUM-VALUES: %d', len(config.value_stack))
        #logger.debug('NUM-LABELS: %d', len(config.label_stack))
        #logger.debug('NUM-FRAMES: %d', len(config.frame_stack))
        #logger.debug('VALUES: %s', tuple(config.value_stack))

        logic_fn = opcode2exec[instruction.opcode][0]
        logic_fn(config)

    if len(config.value_stack) > 1:
        raise Exception("Invariant?")
    else:
        return tuple(config.value_stack)


#############
# 4.5 MODULES
#############

# 4.5.1 EXTERNAL TYPING

def spec_external_typing(S: Store,
                         extern_desc: TExportAddress,
                         ) -> TExportValue:
    logger.debug('spec_external_typing(%s)', extern_desc)

    if isinstance(extern_desc, FunctionAddress):
        if len(S["funcs"]) < extern_desc:
            raise Unlinkable("unlinkable")
        funcinst = S["funcs"][extern_desc]
        return funcinst.type
    elif isinstance(extern_desc, TableAddress):
        if len(S["tables"]) < extern_desc:
            raise Unlinkable("unlinkable")
        tableinst = S["tables"][extern_desc]
        return TableType(
            limits=Limits(UInt32(len(tableinst.elem)), tableinst.max),
            elem_type=FunctionAddress,
        )
    elif isinstance(extern_desc, MemoryAddress):
        if len(S["mems"]) < extern_desc:
            raise Unlinkable("unlinkable")
        meminst = S["mems"][extern_desc]
        return MemoryType(
            UInt32(len(meminst.data) // constants.PAGE_SIZE_64K),
            meminst.max,
        )
    elif isinstance(extern_desc, GlobalAddress):
        if len(S["globals"]) < extern_desc:
            raise Unlinkable("unlinkable")
        globalinst = S["globals"][extern_desc]
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


def spec_allocfunc(S: Store, func: Function, module: ModuleInstance) -> Tuple[Store, FunctionAddress]:
    logger.debug('spec_allocfunc()')

    funcaddr = FunctionAddress(len(S["funcs"]))
    func_type = module.types[func.type]
    funcinst = FunctionInstance(func_type, module, func)
    S["funcs"].append(funcinst)
    return S, funcaddr


def spec_allochostfunc(S: Store,
                       functype: FunctionType,
                       hostfunc: HostFunctionCallable,
                       ) -> Tuple[Store, FunctionAddress]:
    logger.debug('spec_allochostfunc()')

    funcaddr = FunctionAddress(len(S["funcs"]))
    funcinst = HostFunction(functype, hostfunc)
    S["funcs"].append(funcinst)
    return S, funcaddr


def spec_alloctable(S: Store, table_type: TableType) -> Tuple[Store, TableAddress]:
    logger.debug('spec_alloctable()')

    tableaddr = TableAddress(len(S["tables"]))
    tableinst = TableInstance(
        elem=[None] * table_type.limits.min,
        max=table_type.limits.max,
    )
    S["tables"].append(tableinst)
    return S, tableaddr


def spec_allocmem(S: Store, memory_type: MemoryType) -> Tuple[Store, MemoryAddress]:
    logger.debug('spec_allocmem()')

    memaddr = MemoryAddress(len(S["mems"]))
    meminst = MemoryInstance(
        data=bytearray(memory_type.min * constants.PAGE_SIZE_64K),
        max=memory_type.max,
    )
    S["mems"].append(meminst)
    return S, memaddr


def spec_allocglobal(S: Store,
                     global_type: GlobalType,
                     val: TValue) -> Tuple[Store, GlobalAddress]:
    logger.debug('spec_allocglobal()')

    globaladdr = GlobalAddress(len(S["globals"]))
    globalinst = GlobalInstance(global_type.valtype, val, global_type.mut)
    S["globals"].append(globalinst)
    return S, globaladdr


def spec_growtable(tableinst: TableInstance, n: int) -> TableInstance:
    logger.debug('spec_growtable()')

    len_ = n + len(tableinst.elem)

    if len_ >= constants.UINT32_CEIL:
        # TODO: runtime validation that should be removed
        raise Exception("Invariant")
    elif tableinst.max is not None and tableinst.max < len_:
        # TODO: runtime validation that should be removed
        raise Exception("Invariant")
    else:
        tableinst.elem.extend(itertools.repeat(None, n))

    # TODO: remove return value
    return tableinst


def spec_growmem(meminst: MemoryInstance, n: UInt32) -> Optional[str]:
    logger.debug('spec_growmem()')

    if len(meminst.data) % constants.PAGE_SIZE_64K != 0:
        # TODO: runtime validation that should be removed
        raise Exception("Invariant")

    len_ = n + len(meminst.data) // constants.PAGE_SIZE_64K
    if len_ >= constants.UINT16_CEIL:
        # TODO: remove use of magic strings
        return "fail"
    elif meminst.max is not None and meminst.max < len_:
        # TODO: remove use of magic strings
        return "fail"

    meminst.data.extend(bytearray(
        n * constants.PAGE_SIZE_64K
    ))  # each page created with bytearray(65536) which is 0s

    # TODO: remove return statement
    return None


# TODO: more precise type hint for `Store` return type.
def spec_allocmodule(S: Store,
                     module: Module,
                     externvalimstar: Sequence[TExportAddress],
                     valstar: Tuple[TValue, ...],
                     ) -> Tuple[Store, ModuleInstance]:
    logger.debug('spec_allocmodule()')

    next_function_address = len(S["funcs"])

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
            desc = funcaddrmodstar[exporti.func_idx]
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
            id=uuid.uuid4(),
            module=moduleinstim,
            locals=[],
            instructions=InstructionSequence(globali.init),
            arity=1,
            height=0,
        )
        frame_stack = FrameStack()
        frame_stack.push(F)
        config = Configuration(
            store=S,
            frame_stack=frame_stack,
            value_stack=ValueStack(),
            label_stack=LabelStack(),
        )
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
            id=uuid.uuid4(),
            module=moduleinst,
            locals=[],
            instructions=InstructionSequence(elemi.offset),
            arity=0,
            height=0,
        )
        frame_stack = FrameStack()
        frame_stack.push(F)
        config = Configuration(
            store=S,
            frame_stack=frame_stack,
            value_stack=ValueStack(),
            label_stack=LabelStack()
        )
        eovali = spec_expr(config)[0]
        eoi = eovali
        eo += [eoi]
        tableidxi = elemi.table_idx
        tableaddri = moduleinst.table_addrs[tableidxi]
        tableinsti = S["tables"][tableaddri]
        tableinst += [tableinsti]
        eendi = eoi + len(elemi.init)
        if eendi > len(tableinsti.elem):
            raise Unlinkable("unlinkable")
    # 10
    meminst = []
    do = []
    for datai in module.data:
        F = Frame(
            id=uuid.uuid4(),
            module=moduleinst,
            locals=[],
            instructions=InstructionSequence(datai.offset),
            arity=0,
            height=0,
        )
        frame_stack = FrameStack()
        frame_stack.push(F)
        config = Configuration(
            store=S,
            frame_stack=frame_stack,
            value_stack=ValueStack(),
            label_stack=LabelStack(),
        )
        dovali = spec_expr(config)
        doi = dovali[0]
        do += [doi]
        memidxi = datai.mem_idx
        memaddri = moduleinst.memory_addrs[memidxi]
        meminsti = S["mems"][memaddri]
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
        funcaddr = moduleinst.func_addrs[module.start.func_idx]
        ret = spec_invoke(S, funcaddr, [])
    else:
        ret = None

    return S, moduleinst, ret


# 4.5.5 INVOCATION

# valn looks like [["i32.const",3],["i32.const",199], ...]
def spec_invoke(S, funcaddr, valn):
    logger.debug('spec_invoke()')

    # 1
    if len(S["funcs"]) < funcaddr or funcaddr < 0:
        raise Exception("bad address")
    # 2
    funcinst = S["funcs"][funcaddr]
    # 5
    t1n, t2m = funcinst.type
    # 4
    if len(valn) != len(t1n):
        raise Exception("wrong number of arguments")
    # 5
    for ti, vali in zip(t1n, valn):
        if vali[0][:3] != ti.value:
            raise Exception("argument type mismatch")
    # 6
    value_stack = ValueStack()
    for ti, vali in zip(t1n, valn):
        arg = vali[1]

        value_stack.push(arg)

    # 7
    if isinstance(funcinst, FunctionInstance):
        frame_stack = FrameStack()
        F = Frame(
            id=uuid.uuid4(),
            module=ModuleInstance((), (), (), (), (), ()),
            locals=[],
            instructions=InstructionSequence((InvokeInstruction(funcaddr), End())),
            arity=0,  # should this be 1 (or derived from the function type)?
            height=0,
        )
        frame_stack.push(F)
        config = Configuration(
            store=S,
            frame_stack=frame_stack,
            value_stack=value_stack,
            label_stack=LabelStack(),
        )
        valresm = spec_expr(config)
        assert valresm is not None
        return valresm
    elif isinstance(funcinst, HostFunction):
        S, valresm = funcinst.hostcode(S, value_stack)
        assert valresm is not None
        return valresm
    else:
        raise Exception(f"Invariant: unknown function type: {type(funcinst)}")


###################
###################
# 5 BINARY FORMAT #
###################
###################

# Chapter 5 defines a binary syntax over the abstract syntax. The implementation is a recursive-descent parser which takes a `.wasm` file and builds an abstract syntax tree out of nested Python lists and dicts. Also implemented are inverses (up to a canonical form) which write an abstract syntax tree back to a `.wasm` file.

# 5.1.3 VECTORS


def spec_binary_vec(raw, idx, B):
    idx, num = spec_binary_uN(raw, idx, 32)
    logger.debug('spec_binary_vec(%s, %s)[%d]', idx, B, num)
    xn = []
    for i in range(num):
        idx, x = B(raw, idx)
        xn += [x]
    return idx, xn


def spec_binary_vec_inv(mynode, myfunc):
    n_bytes = spec_binary_uN_inv(len(mynode), 32)
    xn_bytes = bytearray()
    for x in mynode:
        xn_bytes += myfunc(x)
    return n_bytes + xn_bytes


############
# 5.2 VALUES
############

# 5.2.1 BYTES


def spec_binary_byte(raw, idx):
    if len(raw) <= idx:
        raise MalformedModule("malformed")
    return idx + 1, raw[idx]


def spec_binary_byte_inv(node):
    return bytearray([node])


# 5.2.2 INTEGERS

# unsigned
def spec_binary_uN(raw, idx, N):
    logger.debug('spec_binary_uN(%s, %s)', idx, N)

    idx, n = spec_binary_byte(raw, idx)
    if n < 2 ** 7 and n < 2 ** N:
        return idx, n
    elif n >= 2 ** 7 and N > 7:
        idx, m = spec_binary_uN(raw, idx, N - 7)
        return idx, (2 ** 7) * m + (n - 2 ** 7)
    else:
        raise MalformedModule("malformed")


def spec_binary_uN_inv(k: int, N: int) -> bytearray:
    logger.debug('spec_binary_uN_inv(%s, %s)', k, N)

    if k < 2 ** 7 and k < 2 ** N:
        return bytearray([k])
    elif k >= 2 ** 7 and N > 7:
        return bytearray([k % (2 ** 7) + 2 ** 7]) + spec_binary_uN_inv(
            k // (2 ** 7), N - 7
        )
    else:
        raise MalformedModule("malformed")


# signed
def spec_binary_sN(raw, idx, N):
    n = int(raw[idx])
    idx += 1
    if n < 2 ** 6 and n < 2 ** (N - 1):
        return idx, n
    elif 2 ** 6 <= n < 2 ** 7 and n >= 2 ** 7 - 2 ** (N - 1):
        return idx, n - 2 ** 7
    elif n >= 2 ** 7 and N > 7:
        idx, m = spec_binary_sN(raw, idx, N - 7)
        return idx, 2 ** 7 * m + (n - 2 ** 7)
    else:
        raise MalformedModule("malformed")


def spec_binary_sN_inv(k, N):
    if 0 <= k < 2 ** 6 and k < 2 ** N:
        return bytearray([k])
    elif 2 ** 6 <= k + 2 ** 7 < 2 ** 7:  # and k+2**7>=2**7-2**(N-1):
        return bytearray([k + 2 ** 7])
    elif (k >= 2 ** 6 or k < 2 ** 6) and N > 7:  # (k<0 and k+2**7>=2**6)) and N>7:
        return bytearray([k % (2 ** 7) + 2 ** 7]) + spec_binary_sN_inv(
            (k // (2 ** 7)), N - 7
        )
    else:
        raise MalformedModule("malformed")


# uninterpretted integers
def spec_binary_iN(raw, idx, N):
    idx, n = spec_binary_sN(raw, idx, N)
    i = spec_signediN_inv(N, n)
    return idx, i


def spec_binary_iN_inv(i, N):
    return spec_binary_sN_inv(spec_signediN(N, i), N)


# 5.2.3 FLOATING-POINT

# fN::= b*:byte^{N/8} => bytes_{fN}^{-1}(b*)
def spec_binary_fN(raw, idx, N):
    bstar = bytearray([])
    for i in range(N // 8):
        bstar += bytearray([raw[idx]])
        idx += 1
    return idx, spec_bytest_inv(ValType.get_float_type(BitSize(N)), bstar)  # bytearray(bstar)


def spec_binary_fN_inv(node, N):
    return spec_bytest(ValType.get_float_type(N), node)


# 5.2.4 NAMES

# name as UTF-8 codepoints
def spec_binary_name(raw: bytes, idx: int) -> Tuple[int, str]:
    logger.debug('spec_binary_name()')
    idx, bstar = spec_binary_vec(raw, idx, spec_binary_byte)

    try:
        nametxt = bytearray(bstar).decode()
    except UnicodeDecodeError as err:
        raise MalformedModule from err

    return idx, nametxt


def spec_binary_name_inv(chars):
    name_bytes = bytearray()
    for c in chars:
        c = ord(c)
        if c < 0x80:
            name_bytes += bytes([c])
        elif 0x80 <= c < 0x800:
            name_bytes += bytes([(c >> 6) + 0xC0, (c & 0b111111) + 0x80])
        elif 0x800 <= c < 0x10000:
            name_bytes += bytes(
                [(c >> 12) + 0xE0, ((c >> 6) & 0b111111) + 0x80, (c & 0b111111) + 0x80]
            )
        elif 0x10000 <= c < 0x110000:
            name_bytes += bytes(
                [
                    (c >> 18) + 0xF0,
                    ((c >> 12) & 0b111111) + 0x80,
                    ((c >> 6) & 0b111111) + 0x80,
                    (c & 0b111111) + 0x80,
                ]
            )
        else:
            raise Exception("Invariant")
    return bytearray([len(name_bytes)]) + name_bytes


###########
# 5.3 TYPES
###########

# 5.3.1 VALUE TYPES

def spec_binary_valtype(raw: bytes, idx: int) -> Tuple[int, ValType]:
    try:
        valtype = ValType.from_byte(UInt8(raw[idx]))
    except KeyError as err:
        raise MalformedModule(
            "Invalid byte while parsing valtype.  Got '{hex(raw[idx]}: {str(err)}"
        )
    else:
        return idx + 1, valtype


def spec_binary_valtype_inv(valtype: ValType) -> bytearray:
    logger.debug("spec_binary_valtype_inv(%s)", valtype)

    return bytearray([valtype.to_byte()])


# 5.3.2 RESULT TYPES


def spec_binary_blocktype(raw, idx):
    if raw[idx] == 0x40:
        return idx + 1, []
    idx, valtype = spec_binary_valtype(raw, idx)
    return idx, valtype


def spec_binary_blocktype_inv(node):
    logger.debug("spec_binary_blocktype_inv(%s)", node)

    if isinstance(node, list):
        raise Exception("Invariant")
    elif node == tuple():
        return bytearray([0x40])
    else:
        return spec_binary_valtype_inv(node)


# 5.3.3 FUNCTION TYPES


def spec_binary_functype(raw: bytes, idx: int) -> Tuple[int, FunctionType]:
    if raw[idx] != 0x60:
        raise MalformedModule("malformed")
    idx += 1
    idx, t1star = spec_binary_vec(raw, idx, spec_binary_valtype)
    idx, t2star = spec_binary_vec(raw, idx, spec_binary_valtype)
    return idx, FunctionType(tuple(t1star), tuple(t2star))


def spec_binary_functype_inv(func_type: FunctionType) -> bytearray:
    # TODO: this code path isn't excercised in the test suite.
    return (
        bytearray([0x60])
        + spec_binary_vec_inv(func_type.params, spec_binary_valtype_inv)
        + spec_binary_vec_inv(func_type.results, spec_binary_valtype_inv)
    )


# 5.3.4 LIMITS


def spec_binary_limits(raw: bytes, idx: int) -> Tuple[int, Limits]:
    if raw[idx] == 0x00:
        idx, n = spec_binary_uN(raw, idx + 1, 32)
        return idx, Limits(n, None)
    elif raw[idx] == 0x01:
        idx, n = spec_binary_uN(raw, idx + 1, 32)
        idx, m = spec_binary_uN(raw, idx, 32)
        return idx, Limits(n, m)
    else:
        raise InvalidModule(
            "Invalid starting byte for limits type.  Expected starting byte to "
            f"be one of 0x00 or 0x01: Got {hex(raw[idx])}"
        )


def spec_binary_limits_inv(limits: Limits) -> bytearray:
    if limits.max is None:
        return bytearray([0x00]) + spec_binary_uN_inv(limits.min, 32)
    else:
        return (
            bytearray([0x01])
            + spec_binary_uN_inv(limits.min, 32)
            + spec_binary_uN_inv(limits.max, 32)
        )


# 5.3.5 MEMORY TYPES


def spec_binary_memtype(raw: bytes, idx: int) -> Tuple[int, MemoryType]:
    idx, limits = spec_binary_limits(raw, idx)
    return idx, MemoryType(limits.min, limits.max)


def spec_binary_memtype_inv(memory_type: MemoryType) -> bytearray:
    limits = Limits(memory_type.min, memory_type.max)
    return spec_binary_limits_inv(limits)


# 5.3.6 TABLE TYPES


def spec_binary_tabletype(raw: bytes, idx: int) -> Tuple[int, TableType]:
    idx, elem_type = spec_binary_elemtype(raw, idx)
    idx, limits = spec_binary_limits(raw, idx)
    return idx, TableType(limits, elem_type)


def spec_binary_elemtype(raw: bytes, idx: int) -> Tuple[int, Type[FunctionAddress]]:
    if raw[idx] == 0x70:
        return idx + 1, FunctionAddress
    else:
        raise MalformedModule("malformed")


def spec_binary_tabletype_inv(table_type: TableType) -> bytearray:
    return spec_binary_elemtype_inv(table_type.elem_type) + spec_binary_limits_inv(table_type.limits)


def spec_binary_elemtype_inv(elem_type: Type[FunctionAddress]) -> bytearray:
    return bytearray([0x70])


# 5.3.7 GLOBAL TYPES


def spec_binary_globaltype(raw: bytes, idx: int) -> Tuple[int, GlobalType]:
    idx, valtype = spec_binary_valtype(raw, idx)
    idx, mut = spec_binary_mut(raw, idx)
    return idx, GlobalType(mut, valtype)


def spec_binary_mut(raw: bytes, idx: int) -> Tuple[int, Mutability]:
    try:
        mut = Mutability.from_byte(UInt8(raw[idx]))
    except ValueError as err:
        raise MalformedModule(
            "Invalid byte while parsing mut.  Got '{hex(raw[idx]}: {str(err)}"
        )
    else:
        return idx + 1, mut


def spec_binary_globaltype_inv(global_type: GlobalType) -> bytearray:
    return (
        spec_binary_valtype_inv(global_type.valtype) +
        spec_binary_mut_inv(global_type.mut)
    )


def spec_binary_mut_inv(mut: Mutability) -> bytearray:
    return bytearray([mut.to_byte()])


##################
# 5.4 INSTRUCTIONS
##################

# 5.4.1-5 VARIOUS INSTRUCTIONS


def spec_binary_memarg(raw, idx):
    idx, a = spec_binary_uN(raw, idx, 32)
    idx, o = spec_binary_uN(raw, idx, 32)
    return idx, {"align": a, "offset": o}


def spec_binary_memarg_inv(node):
    return spec_binary_uN_inv(node["align"], 32) + spec_binary_uN_inv(
        node["offset"], 32
    )


def spec_binary_instr(raw: bytes, idx: int) -> Tuple[int, BaseInstruction]:
    stream = io.BytesIO(raw)
    stream.seek(idx)

    instruction = cast(BaseInstruction, parse_instruction(stream))
    return stream.tell(), instruction


def spec_binary_instr_inv(node):
    logger.debug("spec_binary_instr_inv(%s)", node)

    if type(node[0]) == str:
        instr_bytes += bytearray([opcodes_text2binary[node[0]]])
    # the rest is for immediates
    elif node[0] in {"block", "loop", "if"}:  # block, loop, if
        instr_bytes += spec_binary_blocktype_inv(node[1])
        instar_bytes = bytearray()
        for n in node[2][:-1]:
            instar_bytes += spec_binary_instr_inv(n)
        if len(node) == 4:  # if with else
            instar_bytes += bytearray([0x05])
            for n in node[3][:-1]:
                instar_bytes += spec_binary_instr_inv(n)
        instar_bytes += bytes([0x0B])
        instr_bytes += instar_bytes
    elif node[0] in {"br", "br_if"}:  # br, br_if
        instr_bytes += spec_binary_labelidx_inv(node[1])
    elif node[0] == "br_table":  # br_table
        instr_bytes += spec_binary_vec_inv(node[1], spec_binary_labelidx_inv)
        instr_bytes += spec_binary_labelidx_inv(node[2])
    elif node[0] == "call":  # call
        instr_bytes += spec_binary_funcidx_inv(node[1])
    elif node[0] == "call_indirect":  # call_indirect
        instr_bytes += spec_binary_typeidx_inv(node[1])
        instr_bytes += bytearray([0x00])
    elif (
        0x20 <= opcodes_text2binary[node[0]] <= 0x24
    ):  # get_local, set_local, tee_local
        instr_bytes += spec_binary_localidx_inv(node[1])
    elif 0x20 <= opcodes_text2binary[node[0]] <= 0x24:  # get_global, set_global
        instr_bytes += spec_binary_globalidx_inv(node[1])
    elif (
        0x28 <= opcodes_text2binary[node[0]] <= 0x3E
    ):  # i32.load, i32.load8_s, i64.store, etc
        instr_bytes += spec_binary_memarg_inv(node[1])
    elif 0x3F <= opcodes_text2binary[node[0]] <= 0x40:  # memory.size, memory.grow
        instr_bytes += bytearray([0x00])
    elif node[0] == "i32.const":  # i32.const
        instr_bytes += spec_binary_iN_inv(node[1], 32)
    elif node[0] == "i64.const":  # i64.const
        instr_bytes += spec_binary_iN_inv(node[1], 64)
    elif node[0] == "f32.const":  # i64.const
        instr_bytes += spec_binary_fN_inv(node[1], 32)
    elif node[0] == "f64.const":  # i64.const
        instr_bytes += spec_binary_fN_inv(node[1], 64)
    else:
        raise Exception("Invariant: unreachable code path")
    return instr_bytes


# 5.4.6 EXPRESSIONS


def spec_binary_expr(raw: bytes, idx: int) -> Tuple[int, Tuple[BaseInstruction, ...]]:
    logger.debug("spec_binary_expr(%s)", idx)
    instar: List[BaseInstruction] = []

    # TODO: open ended loop
    while raw[idx] != 0x0B:
        idx, ins = spec_binary_instr(raw, idx)
        instar += [ins]

    if raw[idx] != 0x0B:
        raise MalformedModule("error")

    tail = cast(Tuple[BaseInstruction, ...], (End(),))
    return idx + 1, tuple(instar) + tail


def spec_binary_expr_inv(expr: Expression) -> bytearray:
    instar_bytes = bytearray()

    for instruction in expr:
        instar_bytes += spec_binary_instr_inv(instruction)

    return instar_bytes


#############
# 5.5 MODULES
#############

# 5.5.1 INDICES


def spec_binary_typeidx(raw: bytes, idx: int) -> Tuple[int, TypeIdx]:
    idx, x = spec_binary_uN(raw, idx, 32)
    return idx, TypeIdx(x)


def spec_binary_typeidx_inv(type_idx: TypeIdx) -> bytearray:
    return spec_binary_uN_inv(type_idx, 32)


def spec_binary_funcidx(raw: bytes, idx: int) -> Tuple[int, FuncIdx]:
    idx, x = spec_binary_uN(raw, idx, 32)
    return idx, FuncIdx(x)


def spec_binary_funcidx_inv(func_idx: FuncIdx) -> bytearray:
    return spec_binary_uN_inv(func_idx, 32)


def spec_binary_tableidx(raw: bytes, idx: int) -> Tuple[int, TableIdx]:
    idx, x = spec_binary_uN(raw, idx, 32)
    return idx, TableIdx(x)


def spec_binary_tableidx_inv(table_idx: TableIdx) -> bytearray:
    return spec_binary_uN_inv(table_idx, 32)


def spec_binary_memidx(raw: bytes, idx: int) -> Tuple[int, MemoryIdx]:
    idx, x = spec_binary_uN(raw, idx, 32)
    return idx, MemoryIdx(x)


def spec_binary_memidx_inv(memory_idx: MemoryIdx) -> bytearray:
    return spec_binary_uN_inv(memory_idx, 32)


def spec_binary_globalidx(raw: bytes, idx: int) -> Tuple[int, GlobalIdx]:
    idx, x = spec_binary_uN(raw, idx, 32)
    return idx, GlobalIdx(x)


def spec_binary_globalidx_inv(global_idx: GlobalIdx) -> bytearray:
    return spec_binary_uN_inv(global_idx, 32)


def spec_binary_localidx(raw, idx):
    idx, x = spec_binary_uN(raw, idx, 32)
    return idx, x


def spec_binary_localidx_inv(node):
    return spec_binary_uN_inv(node, 32)


def spec_binary_labelidx(raw, idx):
    idx, l = spec_binary_uN(raw, idx, 32)
    return idx, l


def spec_binary_labelidx_inv(node):
    return spec_binary_uN_inv(node, 32)


# 5.5.2 SECTIONS


def spec_binary_sectionN(raw, idx, N, B, skip):
    logger.debug('spec_binary_section(%s, %s, %s, %s)', idx, N, B, skip)
    if idx >= len(raw):
        return idx, []  # already at end
    elif raw[idx] != N:
        return idx, []  # this sec not included

    idx += 1
    idx, size = spec_binary_uN(raw, idx, 32)
    idx_plus_size = idx + size

    if skip:
        return idx + size, []
    elif N == 0:  # custom section
        idx, ret = B(raw, idx, idx + size)
    elif N == 8:  # start section
        idx, ret = B(raw, idx)
    else:
        idx, ret = spec_binary_vec(raw, idx, B)

    if idx != idx_plus_size:
        raise MalformedModule("malformed")
    return idx, ret


def spec_binary_sectionN_inv(cont, Binv, N):
    if cont == None or cont == []:
        return bytearray([])
    N_bytes = bytearray([N])
    cont_bytes = bytearray()
    if N == 8:  # startsec
        cont_bytes = Binv(cont)
    else:
        cont_bytes = spec_binary_vec_inv(cont, Binv)
    size_bytes = spec_binary_uN_inv(len(cont_bytes), 32)
    return N_bytes + size_bytes + cont_bytes


# 5.5.3 CUSTOM SECTION


def spec_binary_customsec(raw, idx, skip):
    customsecstar = []
    idx, customsec = spec_binary_sectionN(raw, idx, 0, spec_binary_custom, skip)
    return idx, customsec


def spec_binary_custom(raw, idx, endidx):
    bytestar = bytearray()
    idx, name = spec_binary_name(raw, idx)
    while idx < endidx:
        idx, byte = spec_binary_byte(raw, idx)
        bytestar += bytearray([byte])
        if idx != endidx:
            idx += 1
    return idx, [name, bytestar]


def spec_binary_customsec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_custom_inv)


def spec_binary_custom_inv(node):
    return spec_binary_name_inv(node[0]) + spec_binary_byte_inv(node[1])  # check this


# 5.5.4 TYPE SECTION


def spec_binary_typesec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 1, spec_binary_functype, skip)


def spec_binary_typesec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_functype_inv, 1)


# 5.5.5 IMPORT SECTION


def spec_binary_importsec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 2, spec_binary_import, skip)


def spec_binary_import(raw: bytes, idx: int) -> Tuple[int, Import]:
    idx, module = spec_binary_name(raw, idx)
    idx, name = spec_binary_name(raw, idx)
    idx, descriptor = spec_binary_importdesc(raw, idx)
    return idx, Import(module, name, descriptor)


def spec_binary_importdesc(raw: bytes, idx: int) -> Tuple[int, TImportDesc]:
    if raw[idx] == 0x00:
        return spec_binary_typeidx(raw, idx + 1)
    elif raw[idx] == 0x01:
        return spec_binary_tabletype(raw, idx + 1)
    elif raw[idx] == 0x02:
        return spec_binary_memtype(raw, idx + 1)
    elif raw[idx] == 0x03:
        return spec_binary_globaltype(raw, idx + 1)
    else:
        raise Exception("Invariant: unreachable code path")


def spec_binary_importsec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_import_inv, 2)


def spec_binary_import_inv(import_: Import) -> bytearray:
    return (
        spec_binary_name_inv(import_.module)
        + spec_binary_name_inv(import_.name)
        + spec_binary_importdesc_inv(import_.desc)
    )


def spec_binary_importdesc_inv(descriptor: TImportDesc) -> bytearray:
    # TODO: this function not covered by test suite.
    if isinstance(descriptor, TypeIdx):
        return bytearray([0x00]) + spec_binary_typeidx_inv(descriptor)
    elif isinstance(descriptor, TableType):
        return bytearray([0x01]) + spec_binary_tabletype_inv(descriptor)
    elif isinstance(descriptor, MemoryType):
        return bytearray([0x02]) + spec_binary_memtype_inv(descriptor)
    elif isinstance(descriptor, GlobalType):
        return bytearray([0x03]) + spec_binary_globaltype_inv(descriptor)
    else:
        # TODO: this is likely an invariant, needs testing.
        return bytearray()


# 5.5.6 FUNCTION SECTION


def spec_binary_funcsec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 3, spec_binary_typeidx, skip)


def spec_binary_funcsec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_typeidx_inv, 3)


# 5.5.7 TABLE SECTION


def spec_binary_tablesec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 4, spec_binary_table, skip)


def spec_binary_table(raw: bytes, idx: int) -> Tuple[int, Table]:
    idx, tt = spec_binary_tabletype(raw, idx)
    return idx, Table(tt)


def spec_binary_tablesec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_table_inv, 4)


def spec_binary_table_inv(table: Table) -> bytearray:
    return spec_binary_tabletype_inv(table.type)


# 5.5.8 MEMORY SECTION


def spec_binary_memsec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 5, spec_binary_mem, skip)


def spec_binary_mem(raw: bytes, idx: int) -> Tuple[int, Memory]:
    idx, memory_type = spec_binary_memtype(raw, idx)
    return idx, Memory(memory_type)


def spec_binary_memsec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_mem_inv, 5)


def spec_binary_mem_inv(memory: Memory) -> bytearray:
    return spec_binary_memtype_inv(memory.type)


# 5.5.9 GLOBAL SECTION


def spec_binary_globalsec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 6, spec_binary_global, skip)


def spec_binary_global(raw: bytes, idx: int) -> Tuple[int, Global]:
    idx, global_type = spec_binary_globaltype(raw, idx)
    idx, init = spec_binary_expr(raw, idx)
    return idx, Global(global_type, init)


def spec_binary_globalsec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_global_inv, 6)


def spec_binary_global_inv(global_: Global) -> bytearray:
    return (
        spec_binary_globaltype_inv(global_.type) +
        spec_binary_expr_inv(global_.init)
    )


# 5.5.10 EXPORT SECTION


def spec_binary_exportsec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 7, spec_binary_export, skip)


def spec_binary_export(raw: bytes, idx: int) -> Tuple[int, Export]:
    idx, name = spec_binary_name(raw, idx)
    idx, desc = spec_binary_exportdesc(raw, idx)
    return idx, Export(name, desc)


def spec_binary_exportdesc(raw: bytes, idx: int) -> Tuple[int, TExportDesc]:
    if raw[idx] == 0x00:
        return spec_binary_funcidx(raw, idx + 1)
    elif raw[idx] == 0x01:
        return spec_binary_tableidx(raw, idx + 1)
    elif raw[idx] == 0x02:
        return spec_binary_memidx(raw, idx + 1)
    elif raw[idx] == 0x03:
        return spec_binary_globalidx(raw, idx + 1)
    else:
        raise Exception("Unreachable code path")


def spec_binary_exportsec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_export_inv, 7)


def spec_binary_export_inv(node):
    return spec_binary_name_inv(node["name"]) + spec_binary_exportdesc_inv(node["desc"])


def spec_binary_exportdesc_inv(desc: TExportDesc) -> bytearray:
    if isinstance(desc, FuncIdx):
        return bytearray([0x00]) + spec_binary_funcidx_inv(desc)
    elif isinstance(desc, TableIdx):
        return bytearray([0x01]) + spec_binary_tableidx_inv(desc)
    elif isinstance(desc, MemoryIdx):
        return bytearray([0x02]) + spec_binary_memidx_inv(desc)
    elif isinstance(desc, GlobalIdx):
        return bytearray([0x03]) + spec_binary_globalidx_inv(desc)
    else:
        # TODO: check if this is a valid code path
        return bytearray()


# 5.5.11 START SECTION


def spec_binary_startsec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 8, spec_binary_start, skip)


def spec_binary_start(raw: bytes, idx: int) -> Tuple[int, StartFunction]:
    idx, func_idx = spec_binary_funcidx(raw, idx)
    return idx, StartFunction(func_idx)


def spec_binary_startsec_inv(node):
    if node == []:
        return bytearray()
    else:
        return spec_binary_sectionN_inv(node, spec_binary_start_inv, 8)


def spec_binary_start_inv(start: StartFunction) -> bytearray:
    return spec_binary_funcidx_inv(start.func_idx)


# 5.5.12 ELEMENT SECTION


def spec_binary_elemsec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 9, spec_binary_elem, skip)


def spec_binary_elem(raw: bytes, idx: int) -> Tuple[int, ElementSegment]:
    idx, table_idx = spec_binary_tableidx(raw, idx)
    idx, offset = spec_binary_expr(raw, idx)
    idx, init = spec_binary_vec(raw, idx, spec_binary_funcidx)
    return idx, ElementSegment(table_idx, offset, init)


def spec_binary_elemsec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_elem_inv, 9)


def spec_binary_elem_inv(element_type: ElementSegment) -> bytearray:
    return (
        spec_binary_tableidx_inv(element_type.table_idx)
        + spec_binary_expr_inv(element_type.offset)
        + spec_binary_vec_inv(element_type.init, spec_binary_funcidx_inv)
    )


# 5.5.13 CODE SECTION


def spec_binary_codesec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 10, spec_binary_code, skip)


def spec_binary_code(raw, idx):
    logger.debug('spec_binary_code(%s)', idx)
    idx, size = spec_binary_uN(raw, idx, 32)
    idx_end = idx + size
    idx, code = spec_binary_func(raw, idx)

    if idx_end != idx:
        raise MalformedModule("malformed")
    elif len(code) >= constants.UINT32_CEIL:
        raise MalformedModule("malformed")
    else:
        return idx, code


def spec_binary_func(raw, idx):
    logger.debug('spec_binary_func(%s)', idx)
    idx, tstarstar = spec_binary_vec(raw, idx, spec_binary_locals)
    num_locals = sum(locals_info.num for locals_info in tstarstar)

    if num_locals > constants.UINT32_MAX:
        raise MalformedModule("malformed")

    idx, e = spec_binary_expr(raw, idx)
    logger.debug('AFTER EXPR: %s', idx)
    concattstarstar = [
        locals_info.valtype
        for locals_info
        in tstarstar
        for _ in range(locals_info.num)
    ]
    return idx, [concattstarstar, e]


class LocalsInfo(NamedTuple):
    num: int
    valtype: ValType


def spec_binary_locals(raw: bytes, idx: int) -> Tuple[int, LocalsInfo]:
    logger.debug("spec_binary_locals(%s)", idx)
    idx, num = spec_binary_uN(raw, idx, 32)
    idx, valtype = spec_binary_valtype(raw, idx)
    return idx, LocalsInfo(num, valtype)


def spec_binary_codesec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_code_inv, 10)


def spec_binary_code_inv(node):
    func_bytes = spec_binary_func_inv(node)
    return spec_binary_uN_inv(len(func_bytes), 32) + func_bytes


def spec_binary_func_inv(node):
    # group locals into chunks
    locals_ = []
    prev_valtype = ""
    for valtype in node[0]:
        if valtype == prev_valtype:
            locals_[-1][0] += 1
        else:
            locals_ += [[1, valtype]]
            prev_valtype = valtype
    locals_bytes = spec_binary_vec_inv(locals_, spec_binary_locals_inv)
    expr_bytes = spec_binary_expr_inv(node[1])
    return locals_bytes + expr_bytes


def spec_binary_locals_inv(node):
    return spec_binary_uN_inv(node[0], 32) + spec_binary_valtype_inv(node[1])


# 5.5.14 DATA SECTION


def spec_binary_datasec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 11, spec_binary_data, skip)


def spec_binary_data(raw: bytes, idx: int) -> Tuple[int, DataSegment]:
    idx, mem_idx = spec_binary_memidx(raw, idx)
    idx, expression = spec_binary_expr(raw, idx)
    idx, init = spec_binary_vec(raw, idx, spec_binary_byte)
    return idx, DataSegment(mem_idx, expression, init)


def spec_binary_datasec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_data_inv, 11)


def spec_binary_data_inv(data: DataSegment) -> bytearray:
    return (
        spec_binary_memidx_inv(data.mem_idx)
        + spec_binary_expr_inv(data.offset)
        + spec_binary_vec_inv(data.init, spec_binary_byte_inv)
    )


# 5.5.15 MODULES


def spec_binary_module(raw: bytes) -> Module:
    idx = 0
    magic = [0x00, 0x61, 0x73, 0x6D]
    if magic != [x for x in raw[idx : idx + 4]]:
        raise MalformedModule("malformed")
    idx += 4
    version = [0x01, 0x00, 0x00, 0x00]
    if version != [x for x in raw[idx : idx + 4]]:
        raise MalformedModule("malformed")
    idx += 4

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, functypestar = spec_binary_typesec(raw, idx, 0)
    logger.debug("functypestar: %s", functypestar)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, importstar = spec_binary_importsec(raw, idx, 0)
    logger.debug("importstar: %s", importstar)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, typeidxn = spec_binary_funcsec(raw, idx, 0)
    logger.debug("typeidxn: %s", typeidxn)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, tablestar = spec_binary_tablesec(raw, idx, 0)
    logger.debug("tablestar: %s", tablestar)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, memstar = spec_binary_memsec(raw, idx, 0)
    logger.debug("memstar: %s", memstar)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, globalstar = spec_binary_globalsec(raw, idx, 0)
    logger.debug("globalstar: %s", globalstar)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, exportstar = spec_binary_exportsec(raw, idx, 0)
    logger.debug("exportstar: %s", exportstar)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, startq = spec_binary_startsec(raw, idx, 0)
    logger.debug("startq: %s", startq)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, elemstar = spec_binary_elemsec(raw, idx, 0)
    logger.debug("elemstar: %s", elemstar)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, coden = spec_binary_codesec(raw, idx, 0)
    logger.debug("coden: %s", coden)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, datastar = spec_binary_datasec(raw, idx, 0)
    logger.debug("datastar: %s", datastar)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    # TODO: It appears that this function incorrectly exits early once it
    # encounters an invalid section id.  See `tests/custom.wast`.

    funcn = []
    if typeidxn and coden and len(typeidxn) == len(coden):
        for i in range(len(typeidxn)):
            funcn.append(Function(typeidxn[i], tuple(coden[i][0]), tuple(coden[i][1])))

    if startq:
        start = startq
    else:
        start = None

    # TODO: remove tuple wrapping
    module = Module(
        types=tuple(functypestar),
        funcs=tuple(funcn),
        tables=tuple(tablestar),
        mems=tuple(memstar),
        globals=tuple(globalstar),
        elem=tuple(elemstar),
        data=tuple(datastar),
        start=start,
        imports=tuple(importstar),
        exports=tuple(exportstar),
    )
    return module


def spec_binary_module_inv_to_file(module: Module, filename: str) -> None:
    f = open(filename, "wb")
    magic = bytes([0x00, 0x61, 0x73, 0x6D])
    version = bytes([0x01, 0x00, 0x00, 0x00])
    f.write(magic)
    f.write(version)
    f.write(spec_binary_typesec_inv(module.types))
    f.write(spec_binary_importsec_inv(module.imports))
    f.write(spec_binary_funcsec_inv([elem.type for elem in module.funcs]))
    f.write(spec_binary_tablesec_inv(module.tables))
    f.write(spec_binary_memsec_inv(module.mems))
    f.write(spec_binary_globalsec_inv(module.globals))
    f.write(spec_binary_exportsec_inv(module.exports))
    f.write(spec_binary_startsec_inv(module.start))
    f.write(spec_binary_elemsec_inv(module.elem))
    f.write(spec_binary_codesec_inv([(f.locals, f.body) for f in module.funcs]))
    f.write(spec_binary_datasec_inv(module.data))
    f.close()


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
    return {"funcs": [], "mems": [], "tables": [], "globals": []}


# 7.1.2 MODULES


def decode_module(bytestar):
    return spec_binary_module(bytestar)


def parse_module(codepointstar):
    raise NotImplementedError("Text parser not yet implemented")


def validate_module(module):
    spec_validate_module(module)


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


def module_imports(module):
    ret = spec_validate_module(module)

    externtypestar, extertypeprimestar = ret
    importstar = module.imports

    if len(importstar) != len(externtypestar):
        raise InvalidModule(
            f"Wrong import length: expected {len(extertypeprimestar)} / got "
            f"{len(externtypestar)}"
        )

    result = []
    for importi, externtypei in zip(importstar, externtypestar):
        # This code path appears to be missing test coverage.
        resutli = [importi.module, importi.name, externtypei]
        result += resulti
    return result


def module_exports(module):
    ret = spec_validate_module(mod)

    externtypestar, extertypeprimestar = ret
    exportstar = module.exports

    if len(exportstar) != len(externtypeprimestar):
        raise Exception(
            f"Expected {len(exportstar)} exports.  Got "
            f"{len(externtypeprimestar)}"
        )

    # TODO: this code path is not covered by tests
    result = []
    for i in range(len(importstar)):
        exporti = exportstar[i]
        externtypeprimei = externtypeprimestar[i]
        resulti = [exporti["name"], externtypeprimei]
        result += resulti
    return result


# 7.1.3 EXPORTS

def get_export(moduleinst: ModuleInstance, name: str) -> TExportAddress:
    # assume valid so all export names are unique
    for exportinsti in moduleinst.exports:
        if name == exportinsti.name:
            return exportinsti.value
    else:
        known_module_names = sorted(set(export.name for export in moduleinst.exports))
        raise ValidationError(
            f"No module found with name `{name}`.  Known module names: "
            f"{'|'.join(known_module_names)}"
        )


# 7.1.4 FUNCTIONS


def alloc_func(store, functype, hostfunc):
    store, funcaddr = spec_allochostfunc(store, functype, hostfunc)
    return store, funcaddr


def type_func(store, funcaddr):
    if len(store["funcs"]) <= funcaddr:
        raise ValidationError(
            f"Function address outside of allowed range: {funcaddr} > "
            f"{len(store['funcs'])}"
        )
    functype = store["funcs"][funcaddr]
    return functype


def invoke_func(store, funcaddr, valstar):
    ret = spec_invoke(store, funcaddr, valstar)
    return store, ret


# 7.1.4 TABLES


def alloc_table(store, tabletype):
    store, tableaddr = spec_alloctable(store, tabletype)
    return store, tableaddr


def type_table(store, tableaddr):
    if len(store["tables"]) <= tableaddr:
        raise ValidationError(
            f"Table address outside of allowed range: {tableaddr} > "
            f"{len(store['tables'])}"
        )
    tableinst = store["tables"][tableaddr]
    max_ = tableinst.max
    min_ = len(tableinst.elem)
    tabletype = TableType(Limits(min_, max_), FunctionAddress)
    return tabletype


def read_table(store, tableaddr, i):
    if len(store["tables"]) <= tableaddr:
        raise ValidationError(
            f"Table address outside of allowed range: {tableaddr} > "
            f"{len(store['tables'])}"
        )
    if type(i) != int or i < 0:
        raise ValidationError(
            f"Invalid table index.  Must be positive integer.  Got {repr(i)}"
        )
    ti = store["tables"][tableaddr]
    if i >= len(ti.elem):
        raise ValidationError(
            f"Index out of range for table.  {i} >= {len(ti['elem'])}"
        )
    return ti.elem[i]


def write_table(store, tableaddr, i, funcaddr):
    if len(store["tables"]) <= tableaddr:
        raise ValidationError(
            f"Table address outside of allowed range: {tableaddr} > "
            f"{len(store['tables'])}"
        )
    if type(i) != int or i < 0:
        raise ValidationError(
            f"Invalid table index.  Must be positive integer.  Got {repr(i)}"
        )
    ti = store["tables"][tableaddr]
    if i >= len(ti.elem):
        raise ValidationError(
            f"Index out of range for table.  {i} >= {len(ti['elem'])}"
        )
    ti.elem[i] = funcaddr
    return store


def size_table(store, tableaddr):
    if len(store["tables"]) <= tableaddr:
        raise ValidationError(
            f"Table address outside of allowed range: {tableaddr} > "
            f"{len(store['tables'])}"
        )
    return len(store["tables"][tableaddr].elem)


def grow_table(store, tableaddr, n):
    if len(store["tables"]) <= tableaddr:
        raise ValidationError(
            f"Table address outside of allowed range: {tableaddr} > "
            f"{len(store['tables'])}"
        )
    elif type(n) != int or n < 0:
        raise ValidationError(
            f"Invalid table index.  Must be positive integer.  Got {repr(i)}"
        )

    spec_growtable(store["tabless"][tableaddr], n)

    return store


# 7.1.6 MEMORIES


def alloc_mem(store, memtype):
    store, memaddr = spec_allocmem(store, memtype)
    return store, memaddr


def type_mem(store, memaddr):
    if len(store["mems"]) <= memaddr:
        raise ValidationError(
            f"Memory address outside of allowed range: {memaddr} > "
            f"{len(store['mems'])}"
        )
    meminst = store["mems"][memaddr]
    max_ = meminst.max
    min_ = (
        len(meminst.data) // constants.PAGE_SIZE_64K
    )


def read_mem(store, memaddr, i):
    if len(store["mems"]) <= memaddr:
        raise ValidationError(
            f"Memory address outside of allowed range: {memaddr} > "
            f"{len(store['mems'])}"
        )
    elif type(i) != int or i < 0:
        raise ValidationError(
            f"Invalid memory index.  Must be positive integer.  Got {repr(i)}"
        )

    mi = store["mems"][memaddr]

    if i >= len(mi.data):
        raise ValidationError(
            f"Memory index out of bounds.  {i} >= {len(mi['data'])}"
        )
    else:
        return mi.data[i]


def write_mem(store, memaddr, i, byte):
    if len(store["mems"]) <= memaddr:
        raise ValidationError(
            f"Memory address outside of allowed range: {memaddr} > "
            f"{len(store['mems'])}"
        )
    elif type(i) != int or i < 0:
        raise ValidationError(
            f"Invalid memory index.  Must be positive integer.  Got {repr(i)}"
        )

    mi = store["mems"][memaddr]
    if i >= len(mi.data):
        raise ValidationError(
            f"Memory index out of bounds.  {i} >= {len(mi['data'])}"
        )
    mi.data[i] = byte
    return store


def size_mem(store, memaddr):
    if len(store["mems"]) <= memaddr:
        raise ValidationError(
            f"Memory address outside of allowed range: {memaddr} > "
            f"{len(store['mems'])}"
        )
    return len(store["mems"][memaddr]) // constants.PAGE_SIZE_64K


def grow_mem(store, memaddr, n):
    if len(store["mems"]) <= memaddr:
        raise ValidationError(
            f"Memory address outside of allowed range: {memaddr} > "
            f"{len(store['mems'])}"
        )
    elif type(n) != int or n < 0:
        raise ValidationError(
            f"Invalid memory index.  Must be positive integer.  Got {repr(i)}"
        )

    spec_growmem(store["mems"][memaddr], n)

    return store


# 7.1.7 GLOBALS


def alloc_global(store, globaltype, val):
    return spec_allocglobal(store, globaltype, val)


def type_global(store: Store, globaladdr: GlobalAddress) -> GlobalType:
    if len(store["globals"]) <= globaladdr:
        raise ValidationError(
            f"Globals address outside of allowed range: {globaladdr} > "
            f"{len(store['globals'])}"
        )
    globalinst = store["globals"][globaladdr]
    return GlobalType(globalinst.mut, globalinst.valtype)


def read_global(store: Store, globaladdr: GlobalAddress) -> TValue:
    if len(store["globals"]) <= globaladdr:
        raise ValidationError(
            f"Globals address outside of allowed range: {globaladdr} > "
            f"{len(store['globals'])}"
        )
    gi = store["globals"][globaladdr]
    return gi.value


# arg must look like ["i32.const",5]
def write_global(store: Store, globaladdr: GlobalAddress, val: TValue) -> Store:
    if len(store["globals"]) <= globaladdr:
        raise ValidationError(
            f"Globals address outside of allowed range: {globaladdr} > "
            f"{len(store['globals'])}"
        )
    # TODO: type check; handle val without type
    gi = store["globals"][globaladdr]
    if gi.mut is not Mutability.var:
        raise ValidationError("Attempt to write to an immutable global variable at address '{globaladdr}'")
    store["globals"][globaladdr] = GlobalInstance(gi.valtype, val, gi.mut)
    return store


##########################
# 7.3 VALIDATION ALGORITHM
##########################

# 7.3.1 DATA STRUCTURES

# Conventions:
#   the spec makes opds and ctrls global variables, but we pass them around as arguments
#   the control stack is a python list, which allows fast appending but not prepending. So the spec's index 0 corresponds to python list idx -1, and eg spec idx 3 corresponds to our python list idx -1-3 ie -4
#   the spec offers two ways to keep track of labels, using C.labels in ch 3 or a control stack in the appendix. Here we use the appendix method


def spec_push_opd(opds, type_):
    logger.debug('spec_push_opd(%s, %s)', len(opds), type_)
    opds.append(type_)


def spec_pop_opd(opds, ctrls):
    logger.debug('spec_pop_opd(%s, %s)', len(opds), len(ctrls))
    # check if underflows current block, and returns one type but if underflows
    # and unreachable, which can happen if unconditional branch, when stack is
    # typed polymorphically, operands are still pushed and popped to check if
    # code after unreachable is valid, polymorphic stack can't underflow
    if len(opds) == ctrls[-1]["height"] and ctrls[-1]["unreachable"]:
        # TODO: remove magic string usage.
        return "Unknown"
    elif len(opds) == ctrls[-1]["height"]:
        raise InvalidModule("invalid")  # error
    elif len(opds) == 0:
        raise InvalidModule("invalid")  # error, not in spec
    else:
        to_return = opds[-1]
        del opds[-1]
        return to_return


def spec_pop_opd_expect(opds, ctrls, expect):
    logger.debug('spec_pop_opd_expect(%s, %s, %s)', len(opds), len(ctrls), expect)
    actual = spec_pop_opd(opds, ctrls)

    if actual == "Unknown":
        return expect
    elif expect == "Unknown":
        return actual
    elif actual != expect:
        raise InvalidModule("invalid")  # error
    else:
        return actual


def spec_push_opds(opds, ctrls, types):
    logger.debug('spec_push_opds(%s, %s, %s)', len(opds), len(ctrls), types)
    for t in types:
        spec_push_opd(opds, t)


def spec_pop_opds_expect(opds, ctrls, types):
    logger.debug('spec_pop_opds_expect(%s, %s, %s)', len(opds), len(ctrls), types)
    if types:
        for t in reversed(types):
            r = spec_pop_opd_expect(opds, ctrls, t)


def spec_ctrl_frame(label_types, end_types, height, unreachable):
    logger.debug('spec_ctrl_frame(%s, %s, %s, %s)', label_types, end_types, height, unreachable)
    # args are:
    #   label_types: type of the branch's label, to type-check branches
    #   end_types: result type of the branch, currently Wasm spec allows at most one return value
    #   height: height of opd_stack at start of block, to check that operands do not underflow current block
    #   unreachable: whether remainder of block is unreachable, to handle stack-polymorphic typing after branches
    return {
        "label_types": label_types,
        "end_types": end_types,
        "height": height,
        "unreachable": unreachable,
    }


def spec_push_ctrl(opds, ctrls, label, out):
    logger.debug('spec_push_ctrl(%s, %s, %s, %s)', len(opds), len(ctrls), label, out)
    frame = {
        "label_types": label,
        "end_types": out,
        "height": len(opds),
        "unreachable": False,
    }
    ctrls.append(frame)


def spec_pop_ctrl(opds, ctrls):
    logger.debug('spec_pop_ctrl(%s, %s)', len(opds), len(ctrls))
    if len(ctrls) < 1:
        raise InvalidModule("invalid")  # error
    frame = ctrls[-1]
    # verify opd stack has right types to exit block, and pops them
    r = spec_pop_opds_expect(opds, ctrls, frame["end_types"])

    # make shure stack is back to original height
    if len(opds) != frame["height"]:
        raise InvalidModule("invalid")  # error
    del ctrls[-1]
    return frame["end_types"]


# extra underscore since spec_unreachable() is used in chapter 4
def spec_unreachable_(opds, ctrls):
    # purge from operand stack, allows stack-polymorphic logic in pop_opd() take effect
    del opds[ctrls[-1]["height"] :]
    ctrls[-1]["unreachable"] = True


# 7.3.2 VALIDATION OF OPCODE SEQUENCES

# validate a single opcode based on current context C, operand stack opds, and control stack ctrls
def spec_validate_opcode(context: Context, opds: Any, ctrls: Any, instruction: BaseInstruction) -> None:
    logger.debug("spec_validate_opcode(%s, %s, %s, %s)", context, opds, ctrls, instruction)
    # C is the context
    # opds is the operand stack
    # ctrls is the control stack
    opcode_binary = instruction.opcode.value
    logger.info('validating opcode: %s', instruction.opcode.text)

    if instruction.opcode.is_control:  # CONTROL INSTRUCTIONS
        if instruction.opcode is BinaryOpcode.UNREACHABLE:
            spec_unreachable_(opds, ctrls)
        elif instruction.opcode is BinaryOpcode.NOP:
            pass
        elif instruction.opcode is BinaryOpcode.BLOCK:
            spec_push_ctrl(opds, ctrls, instruction.result_type, instruction.result_type)  # type: ignore
        elif instruction.opcode is BinaryOpcode.LOOP:
            spec_push_ctrl(opds, ctrls, tuple(), instruction.result_type)  # type: ignore
        elif instruction.opcode is BinaryOpcode.IF:
            spec_pop_opd_expect(opds, ctrls, ValType.i32)
            spec_push_ctrl(opds, ctrls, instruction.result_type, instruction.result_type)  # type: ignore
        elif instruction.opcode is BinaryOpcode.ELSE:
            results = spec_pop_ctrl(opds, ctrls)
            spec_push_ctrl(opds, ctrls, results, results)
        elif instruction.opcode is BinaryOpcode.END:
            results = spec_pop_ctrl(opds, ctrls)
            spec_push_opds(opds, ctrls, results)
        elif instruction.opcode is BinaryOpcode.BR:
            if len(ctrls) <= instruction.label_idx:  # type: ignore
                raise InvalidModule("invalid")
            label_types = ctrls[-1 - instruction.label_idx]["label_types"]  # type: ignore
            spec_pop_opds_expect(opds, ctrls, label_types)
            spec_unreachable_(opds, ctrls)
        elif instruction.opcode is BinaryOpcode.BR_IF:
            if len(ctrls) <= instruction.label_idx:  # type: ignore
                raise InvalidModule("invalid")

            label_types = ctrls[-1 - instruction.label_idx]["label_types"]  # type: ignore
            spec_pop_opd_expect(opds, ctrls, ValType.i32)
            spec_pop_opds_expect(opds, ctrls, label_types)
            spec_push_opds(opds, ctrls, label_types)
        elif instruction.opcode is BinaryOpcode.BR_TABLE:
            if len(ctrls) <= instruction.default_idx:  # type: ignore
                raise InvalidModule("invalid")
            label_types = ctrls[-1 - instruction.default_idx]["label_types"]  # type: ignore
            for label_idx in instruction.label_indices:  # type: ignore
                if (
                    len(ctrls) <= label_idx
                    or ctrls[-1 - label_idx]["label_types"] != label_types
                ):
                    raise InvalidModule("invalid")
            spec_pop_opd_expect(opds, ctrls, ValType.i32)
            spec_pop_opds_expect(opds, ctrls, label_types)
            spec_unreachable_(opds, ctrls)
        elif instruction.opcode is BinaryOpcode.RETURN:
            result_type = context.returns
            spec_pop_opds_expect(opds, ctrls, result_type)
            spec_unreachable_(opds, ctrls)
        elif instruction.opcode is BinaryOpcode.CALL:
            context.validate_func_idx(instruction.func_idx)  # type: ignore

            func_type = context.get_func(instruction.func_idx)  # type: ignore
            spec_pop_opds_expect(opds, ctrls, func_type.params)
            spec_push_opds(opds, ctrls, func_type.results)
        elif instruction.opcode is BinaryOpcode.CALL_INDIRECT:
            context.validate_table_idx(0)
            table_type = context.get_table(0)

            if table_type.elem_type is not FunctionAddress:
                raise InvalidModule("invalid")

            context.validate_type_idx(instruction.type_idx)  # type: ignore
            func_type = context.get_type(instruction.type_idx)  # type: ignore

            spec_pop_opd_expect(opds, ctrls, ValType.i32)
            spec_pop_opds_expect(opds, ctrls, func_type.params)
            spec_push_opds(opds, ctrls, func_type.results)
    elif instruction.opcode.is_parametric:
        if instruction.opcode is BinaryOpcode.DROP:
            spec_pop_opd(opds, ctrls)
        elif instruction.opcode is BinaryOpcode.SELECT:
            spec_pop_opd_expect(opds, ctrls, ValType.i32)
            t1 = spec_pop_opd(opds, ctrls)
            t2 = spec_pop_opd_expect(opds, ctrls, t1)
            spec_push_opd(opds, t2)
        else:
            raise Exception("Invariant")
    elif instruction.opcode.is_variable:
        if instruction.opcode is BinaryOpcode.GET_LOCAL:
            context.validate_local_idx(instruction.local_idx)  # type: ignore
            valtype = context.get_local(instruction.local_idx)  # type: ignore
            spec_push_opd(opds, valtype)
        elif instruction.opcode is BinaryOpcode.SET_LOCAL:
            context.validate_local_idx(instruction.local_idx)  # type: ignore
            valtype = context.get_local(instruction.local_idx)  # type: ignore
            spec_pop_opd_expect(opds, ctrls, valtype)
        elif instruction.opcode is BinaryOpcode.TEE_LOCAL:
            context.validate_local_idx(instruction.local_idx)  # type: ignore
            valtype = context.get_local(instruction.local_idx)  # type: ignore
            spec_pop_opd_expect(opds, ctrls, valtype)
            spec_push_opd(opds, valtype)
        elif instruction.opcode is BinaryOpcode.GET_GLOBAL:
            context.validate_global_idx(instruction.global_idx)  # type: ignore
            global_ = context.get_global(instruction.global_idx)  # type: ignore
            spec_push_opd(opds, global_.valtype)
        elif instruction.opcode is BinaryOpcode.SET_GLOBAL:
            context.validate_global_idx(instruction.global_idx)  # type: ignore
            global_ = context.get_global(instruction.global_idx)  # type: ignore

            if global_.mut is not Mutability.var:  # type: ignore
                raise InvalidModule("invalid")

            spec_pop_opd_expect(opds, ctrls, global_.valtype)
        else:
            raise Exception(f"Unexpected opcode value: {opcode_binary}")
    elif instruction.opcode.is_memory:
        context.validate_mem_idx(0)

        if instruction.opcode.is_memory_load:
            if 2 ** instruction.memarg.align > instruction.memory_bit_size.value // 8:  # type: ignore
                raise InvalidModule("Invalid memarg alignment")

            spec_pop_opd_expect(opds, ctrls, ValType.i32)
            spec_push_opd(opds, instruction.valtype)  # type: ignore
        elif instruction.opcode.is_memory_store:

            if 2 ** instruction.memarg.align > instruction.memory_bit_size.value // 8:  # type: ignore
                raise InvalidModule("Invalid memarg alignment")

            spec_pop_opd_expect(opds, ctrls, instruction.valtype)  # type: ignore
            spec_pop_opd_expect(opds, ctrls, ValType.i32)
        elif instruction.opcode is BinaryOpcode.MEMORY_SIZE:
            spec_push_opd(opds, ValType.i32)
        elif instruction.opcode is BinaryOpcode.MEMORY_GROW:
            spec_pop_opd_expect(opds, ctrls, ValType.i32)
            spec_push_opd(opds, ValType.i32)
        else:
            raise Exception(f"Unexpected opcode value: {opcode_binary}")
    elif instruction.opcode.is_numeric:
        if instruction.opcode.is_numeric_constant:
            spec_push_opd(opds, instruction.valtype)  # type: ignore
        elif opcode_binary <= 0x4F:
            if opcode_binary == 0x45:  # i32.eqz
                spec_pop_opd_expect(opds, ctrls, ValType.i32)
                spec_push_opd(opds, ValType.i32)
            else:  # i32.eq, i32.ne, i32.lt_s, i32.lt_u, i32.gt_s, i32.gt_u, i32.le_s, i32.le_u, i32.ge_s, i32.ge_u
                spec_pop_opd_expect(opds, ctrls, ValType.i32)
                spec_pop_opd_expect(opds, ctrls, ValType.i32)
                spec_push_opd(opds, ValType.i32)
        elif opcode_binary <= 0x5A:
            if opcode_binary == 0x50:  # i64.eqz
                spec_pop_opd_expect(opds, ctrls, ValType.i64)
                spec_push_opd(opds, ValType.i32)
            else:  # i64.eq, i64.ne, i64.lt_s, i64.lt_u, i64.gt_s, i64.gt_u, i64.le_s, i64.le_u, i64.ge_s, i64.ge_u
                spec_pop_opd_expect(opds, ctrls, ValType.i64)
                spec_pop_opd_expect(opds, ctrls, ValType.i64)
                spec_push_opd(opds, ValType.i32)
        elif opcode_binary <= 0x60:  # f32.eq, f32.ne, f32.lt, f32.gt, f32.le, f32.ge
            spec_pop_opd_expect(opds, ctrls, ValType.f32)
            spec_pop_opd_expect(opds, ctrls, ValType.f32)
            spec_push_opd(opds, ValType.i32)
        elif opcode_binary <= 0x66:  # f64.eq, f64.ne, f64.lt, f64.gt, f64.le, f64.ge
            spec_pop_opd_expect(opds, ctrls, ValType.f64)
            spec_pop_opd_expect(opds, ctrls, ValType.f64)
            spec_push_opd(opds, ValType.i32)
        elif opcode_binary <= 0x78:
            if opcode_binary <= 0x69:  # i32.clz, i32.ctz, i32.popcnt
                spec_pop_opd_expect(opds, ctrls, ValType.i32)
                spec_push_opd(opds, ValType.i32)
            else:  # i32.add, i32.sub, i32.mul, i32.div_s, i32.div_u, i32.rem_s, i32.rem_u, i32.and, i32.or, i32.xor, i32.shl, i32.shr_s, i32.shr_u, i32.rotl, i32.rotr
                spec_pop_opd_expect(opds, ctrls, ValType.i32)
                spec_pop_opd_expect(opds, ctrls, ValType.i32)
                spec_push_opd(opds, ValType.i32)
        elif opcode_binary <= 0x8A:
            if opcode_binary <= 0x7B:  # i64.clz, i64.ctz, i64.popcnt
                spec_pop_opd_expect(opds, ctrls, ValType.i64)
                spec_push_opd(opds, ValType.i64)
            else:  # i64.add, i64.sub, i64.mul, i64.div_s, i64.div_u, i64.rem_s, i64.rem_u, i64.and, i64.or, i64.xor, i64.shl, i64.shr_s, i64.shr_u, i64.rotl, i64.rotr
                spec_pop_opd_expect(opds, ctrls, ValType.i64)
                spec_pop_opd_expect(opds, ctrls, ValType.i64)
                spec_push_opd(opds, ValType.i64)
        elif opcode_binary <= 0x98:
            if (
                opcode_binary <= 0x91
            ):  # f32.abs, f32.neg, f32.ceil, f32.floor, f32.trunc, f32.nearest, f32.sqrt,
                spec_pop_opd_expect(opds, ctrls, ValType.f32)
                spec_push_opd(opds, ValType.f32)
            else:  # f32.add, f32.sub, f32.mul, f32.div, f32.min, f32.max, f32.copysign
                spec_pop_opd_expect(opds, ctrls, ValType.f32)
                spec_pop_opd_expect(opds, ctrls, ValType.f32)
                spec_push_opd(opds, ValType.f32)
        elif opcode_binary <= 0xA6:
            if (
                opcode_binary <= 0x9F
            ):  # f64.abs, f64.neg, f64.ceil, f64.floor, f64.trunc, f64.nearest, f64.sqrt,
                spec_pop_opd_expect(opds, ctrls, ValType.f64)
                spec_push_opd(opds, ValType.f64)
            else:  # f64.add, f64.sub, f64.mul, f64.div, f64.min, f64.max, f64.copysign
                spec_pop_opd_expect(opds, ctrls, ValType.f64)
                spec_pop_opd_expect(opds, ctrls, ValType.f64)
                spec_push_opd(opds, ValType.f64)
        elif opcode_binary <= 0xBF:
            if opcode_binary == 0xA7:  # i32.wrap/i64
                spec_pop_opd_expect(opds, ctrls, ValType.i64)
                spec_push_opd(opds, ValType.i32)
            elif opcode_binary <= 0xA9:  # i32.trunc_s/f32, i32.trunc_u/f32
                spec_pop_opd_expect(opds, ctrls, ValType.f32)
                spec_push_opd(opds, ValType.i32)
            elif opcode_binary <= 0xAB:  # i32.trunc_s/f64, i32.trunc_u/f64
                spec_pop_opd_expect(opds, ctrls, ValType.f64)
                spec_push_opd(opds, ValType.i32)
            elif opcode_binary <= 0xAD:  # i64.extend_s/i32, i64.extend_u/i32
                spec_pop_opd_expect(opds, ctrls, ValType.i32)
                spec_push_opd(opds, ValType.i64)
            elif opcode_binary <= 0xAF:  # i64.trunc_s/f32, i64.trunc_u/f32
                spec_pop_opd_expect(opds, ctrls, ValType.f32)
                spec_push_opd(opds, ValType.i64)
            elif opcode_binary <= 0xB1:  # i64.trunc_s/f64, i64.trunc_u/f64
                spec_pop_opd_expect(opds, ctrls, ValType.f64)
                spec_push_opd(opds, ValType.i64)
            elif opcode_binary <= 0xB3:  # f32.convert_s/i32, f32.convert_u/i32
                spec_pop_opd_expect(opds, ctrls, ValType.i32)
                spec_push_opd(opds, ValType.f32)
            elif opcode_binary <= 0xB5:  # f32.convert_s/i64, f32.convert_u/i64
                spec_pop_opd_expect(opds, ctrls, ValType.i64)
                spec_push_opd(opds, ValType.f32)
            elif opcode_binary <= 0xB6:  # f32.demote/f64
                spec_pop_opd_expect(opds, ctrls, ValType.f64)
                spec_push_opd(opds, ValType.f32)
            elif opcode_binary <= 0xB8:  # f64.convert_s/i32, f64.convert_u/i32
                spec_pop_opd_expect(opds, ctrls, ValType.i32)
                spec_push_opd(opds, ValType.f64)
            elif opcode_binary <= 0xBA:  # f64.convert_s/i64, f64.convert_u/i64
                spec_pop_opd_expect(opds, ctrls, ValType.i64)
                spec_push_opd(opds, ValType.f64)
            elif opcode_binary == 0xBB:  # f64.promote/f32
                spec_pop_opd_expect(opds, ctrls, ValType.f32)
                spec_push_opd(opds, ValType.f64)
            elif opcode_binary == 0xBC:  # i32.reinterpret/f32
                spec_pop_opd_expect(opds, ctrls, ValType.f32)
                spec_push_opd(opds, ValType.i32)
            elif opcode_binary == 0xBD:  # i64.reinterpret/f64
                spec_pop_opd_expect(opds, ctrls, ValType.f64)
                spec_push_opd(opds, ValType.i64)
            elif opcode_binary == 0xBE:  # f32.reinterpret/i32
                spec_pop_opd_expect(opds, ctrls, ValType.i32)
                spec_push_opd(opds, ValType.f32)
            elif opcode_binary == 0xBF:  # f64.reinterpret/i64
                spec_pop_opd_expect(opds, ctrls, ValType.i64)
                spec_push_opd(opds, ValType.f64)
            else:
                raise Exception(f"Unexpected opcode value: {opcode_binary}")
        else:
            raise Exception(f"Unexpected opcode value: {opcode_binary}")
    else:
        raise Exception(f"Unexpected opcode value: {opcode_binary}")


BLOCK_LOOP_IF = {
    BinaryOpcode.BLOCK,
    BinaryOpcode.LOOP,
    BinaryOpcode.IF,
}


# args when called the first time:
# TODO: tighten up type hints for `ctrls`
def iterate_through_expression_and_validate_each_opcode(
        expression: Expression, context: Context, opds: List[ValType], ctrls: Any
) -> None:
    for idx, instruction in enumerate(expression):
        if not isinstance(instruction, BaseInstruction):
            raise InvalidModule(
                f"Unrecognized instruction: {repr(instruction)}"
            )

        # validate
        spec_validate_opcode(context, opds, ctrls, instruction)

        # recurse for block, loop, if
        if instruction.opcode in BLOCK_LOOP_IF:
            # arbitrarily use Block to make type checker happy.
            sub_instructions = cast(Block, instruction).instructions
            iterate_through_expression_and_validate_each_opcode(
                sub_instructions, context, opds, ctrls
            )
            if instruction.opcode is BinaryOpcode.IF:
                else_instructions = cast(If, instruction).else_instructions
                iterate_through_expression_and_validate_each_opcode(
                    else_instructions, context, opds, ctrls
                )


##########################################################
# HELPERS TO EXECUTE THIS FILE ON COMMAND LINE ARGUMENTS #
##########################################################


def instantiate_wasm_invoke_start(filename):
    if not os.path.exists(filename):
        raise ValidationError(f"Unable to open file: {filename}")

    with open(filename, 'rb') as file_:
        bytestar = memoryview(file_.read())
        if not bytestar:
            raise ValidationError(f"Error reading file: {filename}")
        module = decode_module(bytestar)  # get module as abstract syntax

    if not module:
        raise ValidationError(f"Could not decode module: {filename}")

    store = init_store()  # do this once for each VM instance
    externvalstar = []  # imports, hopefully none
    store, moduleinst, ret = instantiate_module(store, module, externvalstar)
    return ret


def instantiate_wasm_invoke_func(filename, funcname, args):
    # TODO: DRY: this preamble is the same as the
    # `instantiate_wasm_invoke_start` preamble.
    if not os.path.exists(filename):
        raise ValidationError(f"Unable to open file: {filename}")

    with open(filename, 'rb') as file_:
        bytestar = memoryview(file_.read())
        if not bytestar:
            raise ValidationError(f"Error reading file: {filename}")
        module = decode_module(bytestar)  # get module as abstract syntax

    if not module:
        raise ValidationError(f"Could not decode module: {filename}")

    store = init_store()  # do this once for each VM instance
    externvalstar = []  # imports, hopefully none
    store, moduleinst, ret = instantiate_module(store, module, externvalstar)
    externval = get_export(moduleinst, funcname)

    if not externval or externval[0] != "func":
        raise ValidationError(
            f"No function export found for function name: '{funcname}'"
        )
    funcaddr = externval[1]
    valstar = [["i32.const", int(arg)] for arg in args]
    store, ret = invoke_func(store, funcaddr, valstar)

    if type(ret) == list and len(ret) > 0:
        ret = ret[0]
    return ret
