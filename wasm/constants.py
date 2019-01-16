INT32 = 'i32'
INT64 = 'i64'
FLOAT32 = 'f32'
FLOAT64 = 'f64'

INTEGER_TYPES = {INT32, INT64}
FLOAT_TYPES = {FLOAT32, FLOAT64}

UINT6_CEIL = 2 ** 6

UINT12_CEIL = 2 ** 12

UINT18_CEIL = 2 ** 18

UINT16_CEIL = 2 ** 16

UINT32_CEIL = 2 ** 32
UINT32_MAX = 2 ** 32 - 1

INT32_NEGATIVE_ONE = UINT32_MAX

UINT128_CEIL = 2 ** 128


# https://webassembly.github.io/spec/core/bikeshed/index.html#memory-instances%E2%91%A0
PAGE_SIZE_64K = 65536
