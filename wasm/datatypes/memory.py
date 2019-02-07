from typing import (
    NamedTuple,
    Optional,
)

from wasm import (
    constants,
)
from wasm.exceptions import (
    Trap,
    ValidationError,
)
from wasm.typing import (
    UInt32,
)


class MemoryType(NamedTuple):
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#memory-types%E2%91%A0
    """
    min: UInt32
    max: Optional[UInt32]


class Memory(NamedTuple):
    type: MemoryType


class MemoryInstance(NamedTuple):
    data: bytearray
    max: Optional[UInt32]

    @property
    def num_pages(self) -> UInt32:
        return UInt32(len(self.data) // constants.PAGE_SIZE_64K)

    def read(self, location: UInt32, size: UInt32) -> bytes:
        if location + size > len(self.data):
            raise Trap(
                f"Attempt to read from out of bounds memory location: {location + size} "
                f"> {len(self.data)}"
            )
        return self.data[location:location + size]

    def write(self, location: UInt32, value: bytes) -> None:
        if location + len(value) > len(self.data):
            raise Trap(
                f"Attempt to write to out of bounds memory location: "
                f"{location + len(value)} "
                f"> {len(self.data)}"
            )
        self.data[location: location + len(value)] = value

    def grow(self, num_pages: UInt32) -> UInt32:
        new_num_pages = num_pages + len(self.data) // constants.PAGE_SIZE_64K
        if new_num_pages >= constants.UINT16_CEIL:
            raise ValidationError(
                f"Memory length exceeds u16 bounds: {new_num_pages} > {constants.UINT16_CEIL}"
            )
        elif self.max is not None and self.max < new_num_pages:
            raise ValidationError(
                f"Memory length exceeds maximum memory size bounds: {new_num_pages} > "
                f"{self.max}"
            )

        self.data.extend(bytearray(num_pages * constants.PAGE_SIZE_64K))
        return UInt32(new_num_pages)
