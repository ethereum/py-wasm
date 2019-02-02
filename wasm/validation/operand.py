from typing import (
    Union,
)

from wasm.datatypes import (
    ValType,
)

from .unknown import (
    Unknown,
)

Operand = Union[ValType, Unknown]
