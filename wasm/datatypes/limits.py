from typing import (
    NamedTuple,
    Optional,
)

from wasm.typing import (
    UInt32,
)


class Limits(NamedTuple):
    min: UInt32
    max: Optional[UInt32]
