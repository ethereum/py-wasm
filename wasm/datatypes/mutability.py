import enum


class Mutability(enum.Enum):
    const = 'const'
    var = 'var'

    @classmethod
    def from_byte(cls, byte: int) -> "Mutability":
        if byte == 0x00:
            return cls.const
        elif byte == 0x01:
            return cls.var
        else:
            raise KeyError(
                "Provided byte does not map to a mut type.  Got "
                f"'{hex(byte)}'. Must be one of 0x00 or 0x01."
            )

    def to_byte(self):
        if self is self.const:
            return 0x00
        elif self is self.var:
            return 0x01
        else:
            raise Exception("Invariant")
