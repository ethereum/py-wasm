import logging
from typing import (
    Union,
    cast,
)

import numpy

from wasm import (
    constants,
)
from wasm._utils.numpy import (
    no_overflow,
)
from wasm.exceptions import (
    Trap,
    ValidationError,
)
from wasm.execution import (
    Configuration,
)
from wasm.instructions import (
    MemoryOp,
)

logger = logging.getLogger('wasm.logic.memory')


TInteger = Union[numpy.uint32, numpy.uint64, numpy.int32, numpy.int64]


def load_op(config: Configuration) -> None:
    instruction = cast(MemoryOp, config.instructions.current)
    logger.debug("%s()", instruction.opcode.text)

    memarg = instruction.memarg

    memory_address = config.frame.module.memory_addrs[0]
    mem = config.store.mems[memory_address]

    base_offset = config.pop_u32()
    with no_overflow():
        try:
            memory_location = base_offset + memarg.offset
        except FloatingPointError:
            raise Trap("Memory locatin exceeds u32 bounds: {int(base_offset) + memarg.offset")

    value_bit_width = instruction.memory_bit_size.value
    value_byte_width = value_bit_width // constants.BYTE_SIZE

    raw_bytes = mem.read(memory_location, value_byte_width)

    if instruction.valtype.is_integer_type:
        raw_value = instruction.memory_bit_size.unpack_int_bytes(
            raw_bytes,
            bool(instruction.signed),
        )

        if instruction.signed:
            config.push_operand(instruction.valtype.from_signed(raw_value))
        else:
            config.push_operand(instruction.valtype.value(raw_value))
    elif instruction.valtype.is_float_type:
        value = instruction.valtype.unpack_float_bytes(raw_bytes)
        config.push_operand(value)
    else:
        raise Exception("Invariant")


def store_op(config: Configuration) -> None:
    instruction = cast(MemoryOp, config.instructions.current)
    logger.debug("%s()", instruction.opcode.text)

    memarg = instruction.memarg

    memory_address = config.frame.module.memory_addrs[0]
    mem = config.store.mems[memory_address]

    value = config.pop_operand()

    base_offset = config.pop_u32()
    memory_location = numpy.uint32(base_offset + memarg.offset)

    # TODO: update this section to use the `ValType.pack_bytes` API
    if instruction.valtype.is_integer_type:
        wrapped_value = instruction.memory_bit_size.wrap_type(value)
        encoded_value = wrapped_value.tobytes()
    elif instruction.valtype.is_float_type:
        encoded_value = value.tobytes()
    else:
        raise Exception("Invariant")

    assert len(encoded_value) == instruction.memory_bit_size.value // 8
    mem.write(memory_location, encoded_value)


def memory_size_op(config: Configuration) -> None:
    logger.debug("%s()", config.instructions.current.opcode.text)

    memory_address = config.frame.module.memory_addrs[0]
    mem = config.store.mems[memory_address]
    size = numpy.uint32(len(mem.data) // constants.PAGE_SIZE_64K)
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
