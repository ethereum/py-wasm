from abc import ABC
from typing import (
    TYPE_CHECKING,
    Callable,
    NamedTuple,
    Tuple,
)

from wasm.typing import (
    TValue,
)

from .indices import (
    FunctionIdx,
    TypeIdx,
)
from .valtype import (
    ValType,
)

if TYPE_CHECKING:
    from wasm.instructions import (  # noqa: F401
        BaseInstruction,
    )
    from wasm.execution import (  # noqa: F401
        Configuration,
    )


class FunctionType(NamedTuple):
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#function-types%E2%91%A0
    """
    params: Tuple[ValType, ...]
    results: Tuple[ValType, ...]

    def __str__(self) -> str:
        return f"FunctionType(params={self.params}, results={self.results})"

    def __repr__(self) -> str:
        return str(self)


class Function(NamedTuple):
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#functions%E2%91%A0
    """
    type_idx: TypeIdx
    locals: Tuple[ValType, ...]
    body: Tuple['BaseInstruction', ...]


class BaseFunctionInstance(ABC):
    type: FunctionType


HostFunctionCallable = Callable[['Configuration', Tuple[TValue, ...]], Tuple[TValue, ...]]


class HostFunction(NamedTuple):
    type: FunctionType
    hostcode: HostFunctionCallable


class StartFunction(NamedTuple):
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#syntax-start
    """
    function_idx: FunctionIdx
