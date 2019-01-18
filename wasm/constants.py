from .typing import (
    BitSize,
    UInt32,
)

BITS32 = BitSize(32)
BITS64 = BitSize(64)

UINT6_CEIL = UInt32(2 ** 6)

UINT12_CEIL = UInt32(2 ** 12)

UINT18_CEIL = UInt32(2 ** 18)

UINT16_CEIL = UInt32(2 ** 16)
UINT16_MAX = UInt32(2 ** 16 - 1)

UINT32_CEIL = 2 ** 32
UINT32_MAX = UInt32(2 ** 32 - 1)

INT32_NEGATIVE_ONE = UINT32_MAX

UINT128_CEIL = 2 ** 128


# https://webassembly.github.io/spec/core/bikeshed/index.html#memory-instances%E2%91%A0
PAGE_SIZE_64K = 65536
