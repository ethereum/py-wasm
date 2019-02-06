from typing import (
    TYPE_CHECKING,
    NamedTuple,
    Tuple,
)

from .valtype import (
    ValType,
)

if TYPE_CHECKING:
    from wasm.instructions import (  # noqa: F401
        BaseInstruction,
    )


class LocalsMeta(NamedTuple):
    num: int
    valtype: ValType


class Code(NamedTuple):
    locals: Tuple[ValType, ...]
    expr: Tuple['BaseInstruction', ...]
