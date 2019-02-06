from typing import (
    TYPE_CHECKING,
    NamedTuple,
    Tuple,
)

from .mutability import (
    Mutability,
)
from .valtype import (
    ValType,
)

if TYPE_CHECKING:
    from wasm.typing import (  # noqa: F401
        TValue,
    )
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


class GlobalInstance(NamedTuple):
    # The `valtype` is not part of the spec, but it is useful for inspection.
    valtype: ValType

    value: 'TValue'
    mut: Mutability
