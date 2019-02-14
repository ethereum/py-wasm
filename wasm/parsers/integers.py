from typing import IO

import numpy

from wasm import (
    constants,
)
from wasm.exceptions import (
    MalformedModule,
)

from .leb128 import (
    parse_signed_leb128,
    parse_unsigned_leb128,
)


def parse_s32(stream: IO[bytes]) -> numpy.int32:
    """
    Parser for a single signed 32-bit integer
    """
    start_pos = stream.tell()
    value = parse_signed_leb128(stream)
    end_pos = stream.tell()

    byte_width = end_pos - start_pos

    if byte_width > 5:  # ceil(32 / 7)
        raise MalformedModule(
            f"encoded s32 exceeds maximum byte width: {byte_width} > 5"
        )
    elif constants.SINT32_MIN <= value < constants.SINT32_CEIL:
        return numpy.int32(value)
    elif value < constants.SINT32_MIN:
        raise MalformedModule(
            f"decoded s32 is less than SINT32_MIN: {value} < -1 * 2**31"
        )
    elif value > constants.SINT32_MAX:
        raise MalformedModule(
            f"decoded s32 is greater than SINT32_MAX: {value} > 2**31 - 1"
        )
    else:
        raise Exception("Invariant")


def parse_s64(stream: IO[bytes]) -> numpy.int64:
    """
    Parser for a single signed 64-bit integer
    """
    start_pos = stream.tell()
    value = parse_signed_leb128(stream)
    end_pos = stream.tell()

    byte_width = end_pos - start_pos

    if byte_width > 10:  # ceil(64 / 7)
        raise MalformedModule(
            f"encoded s64 exceeds maximum byte width: {byte_width} > 10"
        )
    elif constants.SINT64_MIN <= value < constants.SINT64_CEIL:
        return numpy.int64(value)
    elif value < constants.SINT64_MIN:
        raise MalformedModule(
            f"decoded s64 is less than SINT64_MIN: {value} < -1 * 2**63"
        )
    elif value > constants.SINT64_MAX:
        raise MalformedModule(
            f"decoded s64 is greater than SINT64_MAX: {value} > 2**63 - 1"
        )
    else:
        raise Exception("Invariant")


def parse_u32(stream: IO[bytes]) -> numpy.uint32:
    """
    Parser for a single unsigned 32-bit integer
    """
    start_pos = stream.tell()
    value = parse_unsigned_leb128(stream)
    end_pos = stream.tell()

    byte_width = end_pos - start_pos

    if byte_width > 5:  # ceil(32 / 7)
        raise MalformedModule(
            f"encoded u32 exceeds maximum byte width: {byte_width} > 5"
        )
    elif constants.UINT32_FLOOR <= value < constants.UINT32_CEIL:
        return numpy.uint32(value)
    elif value < constants.UINT32_FLOOR:
        raise MalformedModule(
            f"decoded uin32 was not positive: {value}"
        )
    elif value > constants.UINT32_MAX:
        raise MalformedModule(
            f"decoded uin32 is greater than UINT32_MAX: {value} > 2**32 - 1"
        )
    else:
        raise Exception("Invariant")


def parse_u64(stream: IO[bytes]) -> numpy.uint64:
    """
    Parser for a single unsigned 64-bit integer
    """
    start_pos = stream.tell()
    value = parse_unsigned_leb128(stream)
    end_pos = stream.tell()

    byte_width = end_pos - start_pos

    if byte_width > 10:  # ceil(64 / 7)
        raise MalformedModule(
            f"encoded u64 exceeds maximum byte width: {byte_width} > 10"
        )
    elif 0 <= value < constants.UINT64_CEIL:
        return numpy.uint64(value)
    elif value < 0:
        raise MalformedModule(
            f"decoded u64 was not positive: {value}"
        )
    elif value > constants.UINT64_MAX:
        raise MalformedModule(
            f"decoded u64 is greater than UINT64_MAX: {value} > 2**64 - 1"
        )
    else:
        raise Exception("Invariant")


def parse_i32(stream: IO[bytes]) -> numpy.uint32:
    """
    Parser for a single i32 value from the WASM spec which are uninterpreted
    integer types.
    """
    value_s = parse_s32(stream)
    value = numpy.uint32(value_s)
    return value


def parse_i64(stream: IO[bytes]) -> numpy.uint64:
    """
    Parser for a single i64 value from the WASM spec which are uninterpreted
    integer types.
    """
    value_s = parse_s64(stream)
    value = numpy.uint64(value_s)
    return value
