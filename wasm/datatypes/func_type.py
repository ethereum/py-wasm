from typing import (
    NamedTuple,
    Tuple,
)

from .val_type import (
    ValType,
)


class FuncType(NamedTuple):
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#function-types%E2%91%A0
    """
    params: Tuple[ValType, ...]
    results: Tuple[ValType, ...]
