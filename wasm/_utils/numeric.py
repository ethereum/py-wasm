from wasm import (
    constants,
)
from wasm.typing import (
    SInt32,
    SInt64,
    UInt32,
    UInt64,
)


def s32_to_u32(value: SInt32) -> UInt32:
    if value < 0:
        return UInt32(value + constants.UINT32_CEIL)
    else:
        return UInt32(value)


def s64_to_u64(value: SInt64) -> UInt64:
    if value < 0:
        return UInt64(value + constants.UINT64_CEIL)
    else:
        return UInt64(value)


def u32_to_s32(value: UInt32) -> SInt32:
    if value > constants.SINT32_MAX:
        return SInt32(value - constants.UINT32_CEIL)
    else:
        return SInt32(value)


def u64_to_s64(value: UInt64) -> SInt64:
    if value > constants.SINT64_MAX:
        return SInt64(value - constants.UINT64_CEIL)
    else:
        return SInt64(value)
