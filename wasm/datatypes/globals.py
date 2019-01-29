from typing import (
    TYPE_CHECKING,
    NamedTuple,
    Tuple,
)

from .mutability import (
    Mutability,
)
from .val_type import (
    ValType,
)

if TYPE_CHECKING:
    from wasm.instructions import (  # noqa: F401
        BaseInstruction,
    )


class GlobalType(NamedTuple):
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#memory-types%E2%91%A0
    """
    mut: Mutability
    valtype: ValType


class Global(NamedTuple):
    type: GlobalType
    init: Tuple['BaseInstruction', ...]
