from typing import (
    NamedTuple,
)

from .mutability import (
    Mutability,
)
from .val_type import (
    ValType,
)


class GlobalType(NamedTuple):
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#memory-types%E2%91%A0
    """
    mut: Mutability
    valtype: ValType
