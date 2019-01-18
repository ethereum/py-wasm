import enum

from wasm import (
    constants,
)
from wasm.typing import (
    BitSize,
    UInt8,
)


class ValType(enum.Enum):
    i32 = 'i32'
    i64 = 'i64'
    f32 = 'f32'
    f64 = 'f64'

    @classmethod
    def from_byte(cls, byte: UInt8) -> 'ValType':
        if byte == 0x7f:
            return cls.i32
        elif byte == 0x7e:
            return cls.i64
        elif byte == 0x7d:
            return cls.f32
        elif byte == 0x7c:
            return cls.f64
        else:
            raise KeyError(
                "Provided byte does not map to a value type.  Got "
                f"'{hex(byte)}'. Must be one of 0x7f|0x7e|0x7d|0x7c"
            )

    @classmethod
    def from_str(cls, type_str: str) -> 'ValType':
        for type_ in cls:
            if type_.value == type_str:
                return type_
        else:
            raise ValueError(
                f"No ValType match for provided type string: '{type_str}'"
            )

    def to_byte(self) -> UInt8:
        if self is self.i32:
            return UInt8(0x7f)
        elif self is self.i64:
            return UInt8(0x7e)
        elif self is self.f32:
            return UInt8(0x7d)
        elif self is self.f64:
            return UInt8(0x7c)
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
        if self is self.i32:
            return constants.BITS32
        elif self is self.i64:
            return constants.BITS64
        elif self is self.f32:
            return constants.BITS32
        elif self is self.f64:
            return constants.BITS64
        else:
            raise Exception("Invariant")

    @classmethod
    def get_float_type(cls, num_bits: BitSize) -> 'ValType':
        if num_bits == 32:
            return cls.f32
        elif num_bits == 64:
            return cls.f64
        else:
            raise ValueError(
                f"Invalid bit size.  Must be 32 or 64: Got {num_bits}"
            )

    @classmethod
    def get_integer_type(cls, num_bits: BitSize) -> 'ValType':
        if num_bits == 32:
            return cls.i32
        elif num_bits == 64:
            return cls.i64
        else:
            raise ValueError(
                f"Invalid bit size.  Must be 32 or 64: Got {num_bits}"
            )
