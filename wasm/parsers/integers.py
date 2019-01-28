import io

from wasm import (
    constants,
)
from wasm._utils.numeric import (
    s32_to_u32,
    s64_to_u64,
)
from wasm.exceptions import (
    MalformedModule,
)
from wasm.typing import (
    SInt32,
    SInt64,
    UInt32,
    UInt64,
)

from .leb128 import (
    parse_signed_leb128,
    parse_unsigned_leb128,
)


def parse_s32(stream: io.BytesIO) -> SInt32:
    start_pos = stream.tell()
    value = parse_signed_leb128(stream)
    end_pos = stream.tell()

    byte_width = end_pos - start_pos

    if byte_width > 5:  # ceil(32 / 7)
        raise MalformedModule(
            f"encoded s32 exceeds maximum byte width: {byte_width} > 10"
        )
    elif constants.SINT32_MIN <= value < constants.SINT32_CEIL:
        return SInt32(value)
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


def parse_s64(stream: io.BytesIO) -> SInt64:
    start_pos = stream.tell()
    value = parse_signed_leb128(stream)
    end_pos = stream.tell()

    byte_width = end_pos - start_pos

    if byte_width > 10:  # ceil(64 / 7)
        raise MalformedModule(
            f"encoded s64 exceeds maximum byte width: {byte_width} > 10"
        )
    elif constants.SINT64_MIN <= value < constants.SINT64_CEIL:
        return SInt64(value)
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


def parse_u32(stream: io.BytesIO) -> UInt32:
    start_pos = stream.tell()
    value = parse_unsigned_leb128(stream)
    end_pos = stream.tell()

    byte_width = end_pos - start_pos

    if byte_width > 5:  # ceil(32 / 7)
        raise MalformedModule(
            f"encoded u32 exceeds maximum byte width: {byte_width} > 10"
        )
    elif 0 <= value < constants.UINT32_CEIL:
        return UInt32(value)
    elif value < 0:
        raise MalformedModule(
            f"decoded uin32 was not positive: {value}"
        )
    elif value > constants.UINT32_MAX:
        raise MalformedModule(
            f"decoded uin32 is greater than UINT32_MAX: {value} > 2**32 - 1"
        )
    else:
        raise Exception("Invariant")


def parse_u64(stream: io.BytesIO) -> UInt64:
    start_pos = stream.tell()
    value = parse_unsigned_leb128(stream)
    end_pos = stream.tell()

    byte_width = end_pos - start_pos

    if byte_width > 10:  # ceil(64 / 7)
        raise MalformedModule(
            f"encoded u64 exceeds maximum byte width: {byte_width} > 10"
        )
    elif 0 <= value < constants.UINT64_CEIL:
        return UInt64(value)
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


def parse_i32(stream: io.BytesIO) -> UInt32:
    value_s = parse_s32(stream)
    value = s32_to_u32(value_s)
    return value


def parse_i64(stream: io.BytesIO) -> UInt64:
    value_s = parse_s64(stream)
    value = s64_to_u64(value_s)
    return value
