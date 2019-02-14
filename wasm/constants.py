import numpy


# Terminology
# -----------
#
# CEIL - a non-inclusive upper bound
# FLOOR - a non-inclusive lower bound
#
# MAX - an inclusive upper bound
# MIN - an inclusive lower bound
#
# UINT - unsigned integer
# SINT - signed integer

UINT6_CEIL = numpy.uint32(2 ** 6)

UINT12_CEIL = numpy.uint32(2 ** 12)

UINT16_CEIL = 2 ** 16
UINT16_MAX = numpy.uint32(2 ** 16 - 1)

UINT18_CEIL = numpy.uint32(2 ** 18)

UINT32_MIN = numpy.uint32(0)
UINT32_MAX = numpy.uint32(2 ** 32 - 1)

UINT32_FLOOR = -1
UINT32_CEIL = 2 ** 32

UINT64_MIN = numpy.uint64(0)
UINT64_MAX = numpy.uint64(2 ** 64 - 1)

UINT64_FLOOR = -1
UINT64_CEIL = 2 ** 64

SINT32_MIN = numpy.int32(-1 * 2 ** 31)
SINT32_MAX = numpy.int32(2 ** 31 - 1)

SINT32_FLOOR = -1 * 2 ** 31 - 1
SINT32_CEIL = 2 ** 31

SINT64_MIN = -1 * 2 ** 63
SINT64_MAX = 2 ** 63 - 1

SINT64_FLOOR = -1 * 2 ** 63 - 1
SINT64_CEIL = 2 ** 63

UINT128_CEIL = 2 ** 128

# The unsigned representation of a -1 for a signed 32 bit integer.
INT32_NEGATIVE_ONE = UINT32_MAX

FLOAT32_MIN = numpy.float32('-3.4028235e+38')
FLOAT32_MAX = numpy.float32('3.4028235e+38')
FLOAT64_MIN = numpy.float64('-1.7976931348623157e+308')
FLOAT64_MAX = numpy.float64('1.7976931348623157e+308')

# https://webassembly.github.io/spec/core/bikeshed/index.html#memory-instances%E2%91%A0
PAGE_SIZE_64K = 65536

# The byte values for the binary encoded version string.
VERSION_1 = (0x01, 0x00, 0x00, 0x00)

# The number of bits in a single byte
BYTE_SIZE = numpy.uint8(8)

# Interned values for u32 zero and one
U32_ZERO = numpy.uint32(0)
U32_ONE = numpy.uint32(1)
