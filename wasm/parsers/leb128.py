import functools
import io
import itertools
import math
import operator
from typing import (
    Iterable,
)

SIGN_MASK = 2**6
REMOVE_SIGN_MASK = 2**6 - 1


def parse_signed_leb128(stream: io.BytesIO) -> int:
    """
    https://en.wikipedia.org/wiki/LEB128
    """
    parts = tuple(_parse_unsigned_leb128(stream))
    part_with_sign = parts[-1]
    shift = 7 * (len(parts) - 1)
    sign = (part_with_sign >> shift) & SIGN_MASK
    part_without_sign = ((part_with_sign >> shift) & REMOVE_SIGN_MASK) << shift
    value = functools.reduce(
        operator.or_,
        itertools.chain(parts[:-1], (part_without_sign,)),
        0,
    )
    if sign:
        return value - 2 ** (7 * len(parts) - 1)
    else:
        return value


LOW_MASK = 2**7 - 1
HIGH_MASK = 2**7


def parse_unsigned_leb128(stream: io.BytesIO) -> int:
    """
    https://en.wikipedia.org/wiki/LEB128
    """
    return functools.reduce(
        operator.or_,
        _parse_unsigned_leb128(stream),
        0,
    )


# The maximum shift width for a 64 bit integer.  We shouldn't have to decode
# integers larger than this.
SHIFT_64_BIT_MAX = int(math.ceil(64 / 7)) * 7


def _parse_unsigned_leb128(stream: io.BytesIO) -> Iterable[int]:
    for shift in itertools.count(0, 7):
        if shift > SHIFT_64_BIT_MAX:
            raise Exception("TODO: better exception msg: Integer is too large...")

        byte = stream.read(1)

        try:
            value = byte[0]
        except IndexError:
            raise Exception("TODO: proper error message for empty stream")

        yield (value & LOW_MASK) << shift

        if not value & HIGH_MASK:
            break
