import enum

from wasm.typing import (
    UInt8,
)


class Mutability(enum.Enum):
    # TODO: once we no longer need these string values, convert to use 0x00 and
    # 0x01 for enum values which simplifies the `to_byte` implementation to
    # simply return `self.value`
    const = 'const'
    var = 'var'

    @classmethod
    def from_byte(cls, byte: UInt8) -> "Mutability":
        if byte == 0x00:
            return cls.const
        elif byte == 0x01:
            return cls.var
        else:
            raise ValueError(
                "Provided byte does not map to a mut type.  Got "
                f"'{hex(byte)}'. Must be one of 0x00 or 0x01."
            )

    def to_byte(self) -> UInt8:
        if self is self.const:
            return UInt8(0x00)
        elif self is self.var:
            return UInt8(0x01)
        else:
            raise Exception("Invariant")
