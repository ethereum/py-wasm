from typing import (
    TYPE_CHECKING,
    NamedTuple,
    Tuple,
)

from .indices import (
    FuncIdx,
    TypeIdx,
)
from .val_type import (
    ValType,
)

if TYPE_CHECKING:
    from wasm.instructions import (  # noqa: F401
        BaseInstruction,
    )


class FunctionType(NamedTuple):
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#function-types%E2%91%A0
    """
    params: Tuple[ValType, ...]
    results: Tuple[ValType, ...]


class Function(NamedTuple):
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#functions%E2%91%A0
    """
    type: TypeIdx
    locals: Tuple[ValType, ...]
    body: Tuple['BaseInstruction', ...]


class StartFunction(NamedTuple):
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#syntax-start
    """
    func_idx: FuncIdx
