import enum
from typing import (
    Type,
    Union,
)

import numpy

TWrapType = Union[
    Type[numpy.uint8],
    Type[numpy.uint16],
    Type[numpy.uint32],
    Type[numpy.uint64],
]
TUnpack = Union[
    numpy.int8,
    numpy.int16,
    numpy.int32,
    numpy.int64,
    numpy.uint8,
    numpy.uint16,
    numpy.uint32,
    numpy.uint64,
]


class BitSize(enum.Enum):
    b8 = numpy.uint8(8)
    b16 = numpy.uint8(16)
    b32 = numpy.uint8(32)
    b64 = numpy.uint8(64)

    def unpack_int_bytes(self, raw_bytes: bytes, signed: bool) -> TUnpack:
        if self is self.b8:
            if signed:
                return numpy.frombuffer(raw_bytes, numpy.int8)[0]
            else:
                return numpy.frombuffer(raw_bytes, numpy.uint8)[0]
        elif self is self.b16:
            if signed:
                return numpy.frombuffer(raw_bytes, numpy.int16)[0]
            else:
                return numpy.frombuffer(raw_bytes, numpy.uint16)[0]
        elif self is self.b32:
            if signed:
                return numpy.frombuffer(raw_bytes, numpy.int32)[0]
            else:
                return numpy.frombuffer(raw_bytes, numpy.uint32)[0]
        elif self is self.b64:
            if signed:
                return numpy.frombuffer(raw_bytes, numpy.int64)[0]
            else:
                return numpy.frombuffer(raw_bytes, numpy.uint64)[0]
        else:
            raise Exception("Invariant")

    @property
    def wrap_type(self) -> TWrapType:
        if self is self.b8:
            return numpy.uint8
        elif self is self.b16:
            return numpy.uint16
        elif self is self.b32:
            return numpy.uint32
        elif self is self.b64:
            return numpy.uint64
        else:
            raise Exception("Invariant")
