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
