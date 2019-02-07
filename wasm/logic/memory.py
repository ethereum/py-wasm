import logging
import struct
from typing import (
    Dict,
    Optional,
    Tuple,
    Union,
    cast,
)

from wasm import (
    constants,
)
from wasm._utils.numeric import (
    s32_to_u32,
    s64_to_u64,
)
from wasm.datatypes import (
    BitSize,
    ValType,
)
from wasm.exceptions import (
    ValidationError,
)
from wasm.execution import (
    Configuration,
)
from wasm.instructions import (
    MemoryOp,
)
from wasm.typing import (
    SInt32,
    SInt64,
    UInt32,
    UInt64,
)

logger = logging.getLogger('wasm.logic.memory')


TInteger = Union[UInt32, UInt64, SInt32, SInt64]

PARSER_LOOKUP: Dict[Tuple[BitSize, Optional[bool]], str] = {
    (BitSize.b8, True): '<b',
    (BitSize.b8, False): '<B',
    (BitSize.b8, None): '<B',
    (BitSize.b16, True): '<h',
    (BitSize.b16, False): '<H',
    (BitSize.b16, None): '<H',
    (BitSize.b32, True): '<i',
    (BitSize.b32, False): '<I',
    (BitSize.b32, None): '<I',
    (BitSize.b64, True): '<q',
    (BitSize.b64, False): '<Q',
    (BitSize.b64, None): '<Q',
}


def load_op(config: Configuration) -> None:
    instruction = cast(MemoryOp, config.instructions.current)
    logger.debug("%s()", instruction.opcode.text)

    memarg = instruction.memarg

    memory_address = config.frame.module.memory_addrs[0]
    mem = config.store.mems[memory_address]

    base_offset = config.pop_u32()
    memory_location = UInt32(base_offset + memarg.offset)

    value_bit_width = instruction.memory_bit_size.value
    value_byte_width = value_bit_width // 8

    raw_bytes = mem.read(memory_location, value_byte_width)
    fmt = PARSER_LOOKUP[(instruction.memory_bit_size, instruction.signed)]

    value = struct.unpack(fmt, raw_bytes)[0]

    if not instruction.signed:
        config.push_operand(value)
    elif instruction.valtype is ValType.i32:
        config.push_operand(s32_to_u32(value))
    elif instruction.valtype is ValType.i64:
        config.push_operand(s64_to_u64(value))
    else:
        raise Exception("Invariant")


ENCODER_LOOKUP: Dict[BitSize, str] = {
    BitSize.b8: '<B',
    BitSize.b16: '<H',
    BitSize.b32: '<I',
    BitSize.b64: '<Q',
}


def store_op(config: Configuration) -> None:
    instruction = cast(MemoryOp, config.instructions.current)
    logger.debug("%s()", instruction.opcode.text)

    memarg = instruction.memarg

    memory_address = config.frame.module.memory_addrs[0]
    mem = config.store.mems[memory_address]

    value = config.pop_operand()

    base_offset = config.pop_u32()
    memory_location = UInt32(base_offset + memarg.offset)

    if instruction.valtype.is_integer_type:
        fmt = ENCODER_LOOKUP[instruction.memory_bit_size]
        wrapped_value = value % (2 ** instruction.memory_bit_size.value)
        encoded_value = struct.pack(fmt, wrapped_value)
    elif instruction.valtype is ValType.f32:
        encoded_value = struct.pack('<f', value)
    elif instruction.valtype is ValType.f64:
        encoded_value = struct.pack('<d', value)
    else:
        raise Exception("Invariant")

    assert len(encoded_value) == instruction.memory_bit_size.value // 8
    mem.write(memory_location, encoded_value)


def memory_size_op(config: Configuration) -> None:
    logger.debug("%s()", config.instructions.current.opcode.text)

    memory_address = config.frame.module.memory_addrs[0]
    mem = config.store.mems[memory_address]
    size = UInt32(len(mem.data) // constants.PAGE_SIZE_64K)
    config.push_operand(size)


def memory_grow_op(config: Configuration) -> None:
    logger.debug("%s()", config.instructions.current.opcode.text)

    memory_address = config.frame.module.memory_addrs[0]
    mem = config.store.mems[memory_address]
    current_num_pages = mem.num_pages
    num_pages = config.pop_u32()

    try:
        mem.grow(num_pages)
    except ValidationError:
        config.push_operand(constants.INT32_NEGATIVE_ONE)
    else:
        config.push_operand(current_num_pages)
