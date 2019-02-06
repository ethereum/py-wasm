from .typing import (
    SInt32,
    SInt64,
    UInt32,
    UInt64,
)

UINT6_CEIL = UInt32(2 ** 6)

UINT12_CEIL = UInt32(2 ** 12)

UINT18_CEIL = UInt32(2 ** 18)

UINT16_CEIL = UInt32(2 ** 16)
UINT16_MAX = UInt32(2 ** 16 - 1)

UINT32_CEIL = 2 ** 32
UINT32_MAX = UInt32(2 ** 32 - 1)

UINT64_CEIL = 2 ** 64
UINT64_MAX = UInt64(2 ** 64 - 1)

SINT32_CEIL = 2 ** 31
SINT32_MAX = SInt32(2 ** 31 - 1)
SINT32_MIN = SInt32(-1 * 2 ** 31)

SINT64_CEIL = 2 ** 63
SINT64_MAX = SInt64(2 ** 63 - 1)
SINT64_MIN = SInt64(-1 * 2 ** 63)

INT32_NEGATIVE_ONE = UINT32_MAX

UINT128_CEIL = 2 ** 128


# https://webassembly.github.io/spec/core/bikeshed/index.html#memory-instances%E2%91%A0
PAGE_SIZE_64K = 65536

VERSION_1 = (0x01, 0x00, 0x00, 0x00)
