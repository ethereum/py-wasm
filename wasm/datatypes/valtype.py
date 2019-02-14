import enum
from typing import (
    Tuple,
    Type,
    Union,
)

import numpy

from wasm import (
    constants,
)
from wasm.exceptions import (
    ValidationError,
)
from wasm.typing import (
    AnyFloat,
    AnyUnsigned,
    TValue,
)

from .bit_size import (
    BitSize,
)

UINT64_BYTE = numpy.uint8(0x7e)
FLOAT64_BYTE = numpy.uint8(0x7c)
UINT32_BYTE = numpy.uint8(0x7f)
FLOAT32_BYTE = numpy.uint8(0x7d)

UINT64_STR = 'i64'
FLOAT64_STR = 'f64'
UINT32_STR = 'i32'
FLOAT32_STR = 'f32'


AnyInteger = Union[int, numpy.int32, numpy.int64, numpy.uint32, numpy.uint64]
AnySignedInteger = Union[int, numpy.int32, numpy.int64]


class ValType(enum.Enum):
    i32 = numpy.uint32
    i64 = numpy.uint64
    f32 = numpy.float32
    f64 = numpy.float64

    def __str__(self) -> str:
        if self is self.i32:
            return 'i32'
        elif self is self.i64:
            return 'i64'
        elif self is self.f32:
            return 'f32'
        elif self is self.f64:
            return 'f64'
        else:
            raise Exception("Invariant")

    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def from_byte(cls, byte: numpy.uint8) -> 'ValType':
        if byte == UINT64_BYTE:
            return cls.i64
        elif byte == FLOAT64_BYTE:
            return cls.f64
        elif byte == UINT32_BYTE:
            return cls.i32
        elif byte == FLOAT32_BYTE:
            return cls.f32
        else:
            raise ValueError(
                "Provided byte does not map to a value type.  Got "
                f"'{hex(byte)}'. Must be one of 0x7f|0x7e|0x7d|0x7c"
            )

    @classmethod
    def from_str(cls, type_str: str) -> 'ValType':
        if type_str == UINT64_STR:
            return cls.i64
        elif type_str == UINT32_STR:
            return cls.i32
        elif type_str == FLOAT64_STR:
            return cls.f64
        elif type_str == FLOAT32_STR:
            return cls.f32
        else:
            raise ValueError(
                f"No ValType match for provided type string: '{type_str}'"
            )

    def to_byte(self) -> numpy.uint8:
        if self is self.i64:
            return UINT64_BYTE
        elif self is self.f64:
            return FLOAT64_BYTE
        elif self is self.i32:
            return UINT32_BYTE
        elif self is self.f32:
            return FLOAT32_BYTE
        else:
            raise Exception("Invariant")

    @property
    def is_integer_type(self) -> bool:
        return self in {self.i32, self.i64}

    @property
    def is_float_type(self) -> bool:
        return self in {self.f32, self.f64}

    @property
    def bit_size(self) -> BitSize:
        if self is self.i64:
            return BitSize.b64
        elif self is self.f64:
            return BitSize.b64
        elif self is self.i32:
            return BitSize.b32
        elif self is self.f32:
            return BitSize.b32
        else:
            raise Exception("Invariant")

    @classmethod
    def get_float_type(cls, num_bits: BitSize) -> 'ValType':
        if num_bits is BitSize.b64:
            return cls.f64
        elif num_bits is BitSize.b32:
            return cls.f32
        else:
            raise ValueError(
                f"Invalid bit size.  Must be 32 or 64: Got {num_bits}"
            )

    @classmethod
    def get_integer_type(cls, num_bits: BitSize) -> 'ValType':
        if num_bits == BitSize.b64:
            return cls.i64
        elif num_bits == BitSize.b32:
            return cls.i32
        else:
            raise ValueError(
                f"Invalid bit size.  Must be 32 or 64: Got {num_bits}"
            )

    def validate_arg(self, arg):
        if self.is_integer_type:
            if self is self.i64:
                lower, upper = (0, constants.UINT64_MAX)
                type_ = numpy.uint64
            elif self is self.i32:
                lower, upper = (0, constants.UINT32_MAX)
                type_ = numpy.uint32
            else:
                raise Exception("Invariant")

            if not isinstance(arg, type_) or arg < lower or arg > upper:
                raise ValidationError(f"Invalid argument for {self.value}: {arg}")
        elif self.is_float_type:
            if self is self.f64:
                lower, upper = (constants.FLOAT64_MIN, constants.FLOAT64_MAX)
                type_ = numpy.float64
            elif self is self.f32:
                lower, upper = (constants.FLOAT32_MIN, constants.FLOAT32_MAX)
                type_ = numpy.float32
            else:
                raise Exception("Invariant")

            if not isinstance(arg, type_):
                raise ValidationError(f"Invalid argument for {self.value}: {arg}")

            if numpy.isnan(arg) or numpy.isinf(arg):
                pass
            elif arg < lower or arg > upper:
                raise ValidationError(f"Invalid argument for {self.value}: {arg}")
        else:
            raise Exception("Invariant")

    @property
    def zero(self) -> TValue:
        return self.value(0)

    @property
    def negzero(self) -> TValue:
        if self.is_float_type:
            return self.value(-0.0)
        else:
            raise TypeError(f"`-0.0` not defined for type {self}")

    @property
    def negone(self) -> TValue:
        if self.is_float_type:
            return self.value(-1.0)
        else:
            raise TypeError(f"`-1` not defined for type {self}")

    def to_signed(self, value: AnyUnsigned) -> AnySignedInteger:
        if self is self.i64:
            return numpy.int64(value)
        elif self is self.i32:
            return numpy.int32(value)
        else:
            raise TypeError(f"Cannot convert {self} to signed integer")

    def from_signed(self, value: AnySignedInteger) -> TValue:
        if self is self.i64:
            return numpy.uint64(value)
        elif self is self.i32:
            return numpy.uint32(value)
        else:
            raise TypeError(f"Cannot convert {self} to unsigned integer")

    @property
    def signed_type(self) -> Union[Type[numpy.int32], Type[numpy.int64]]:
        if self is self.i64:
            return numpy.int64
        elif self is self.i32:
            return numpy.int32
        else:
            raise TypeError(f"Cannot convert {self} to unsigned integer")

    def to_float(self, value: AnyInteger) -> AnyFloat:
        if self is self.f64:
            return numpy.float64(value)
        elif self is self.f32:
            return numpy.float32(value)
        else:
            raise TypeError(f"Cannot convert {self} to float")

    @property
    def bounds(self) -> Tuple[TValue, TValue]:
        if self is self.i64:
            return (constants.UINT64_MIN, constants.UINT64_MAX)
        elif self is self.f64:
            return (constants.FLOAT64_MIN, constants.FLOAT64_MAX)
        elif self is self.i32:
            return (constants.UINT32_MIN, constants.UINT32_MAX)
        elif self is self.f32:
            return (constants.FLOAT32_MIN, constants.FLOAT32_MAX)
        else:
            raise Exception("Invariant")

    @property
    def mod(self) -> int:
        if self is self.i64:
            return constants.UINT64_CEIL
        elif self is self.i32:
            return constants.UINT32_CEIL
        else:
            raise TypeError(f"mod not valid for type {self}")

    @property
    def signed_bounds(self) -> Tuple[int, int]:
        if self is self.i64:
            return (constants.SINT64_MIN, constants.SINT64_MAX)
        elif self is self.i32:
            return (constants.SINT32_MIN, constants.SINT32_MAX)
        else:
            raise TypeError(f"Cannot convert {self} to unsigned integer")

    def unpack_int_bytes(self, raw_bytes: bytes, signed: bool) -> AnyInteger:
        if self is self.i64:
            if signed:
                return numpy.frombuffer(raw_bytes, numpy.int64)[0]
            else:
                return numpy.frombuffer(raw_bytes, numpy.uint64)[0]
        elif self is self.i32:
            if signed:
                return numpy.frombuffer(raw_bytes, numpy.int32)[0]
            else:
                return numpy.frombuffer(raw_bytes, numpy.uint32)[0]
        else:
            raise TypeError(f"Cannot unpack value of type {self}")

    def unpack_float_bytes(self, raw_bytes: bytes) -> AnyFloat:
        if self is self.f64:
            return numpy.frombuffer(raw_bytes, numpy.float64)[0]
        elif self is self.f32:
            return numpy.frombuffer(raw_bytes, numpy.float32)[0]
        else:
            raise TypeError(f"Cannot unpack value of type {self}")

    @property
    def nan(self) -> AnyFloat:
        if self.is_float_type:
            return self.value('nan')
        else:
            raise TypeError(f"`nan` not defined for type {self}")

    @property
    def negnan(self) -> AnyFloat:
        if self.is_float_type:
            return self.value('-nan')
        else:
            raise TypeError(f"`-nan` not defined for type {self}")

    @property
    def inf(self) -> AnyFloat:
        if self.is_float_type:
            return self.value('inf')
        else:
            raise TypeError(f"`inf` not defined for type {self}")

    @property
    def neginf(self) -> AnyFloat:
        if self.is_float_type:
            return self.value('-inf')
        else:
            raise TypeError(f"`-inf` not defined for type {self}")
