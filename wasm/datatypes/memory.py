from typing import (
    NamedTuple,
    Optional,
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
