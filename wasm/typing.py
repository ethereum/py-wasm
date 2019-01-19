from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    NewType,
    Union,
)

if TYPE_CHECKING:
    from wasm.datatypes import (  # noqa: F401
        FuncIdx,
        GlobalIdx,
        MemoryIdx,
        TableIdx,
    )


Store = Dict[Any, Any]
Module = Dict[Any, Any]
Context = Dict[Any, Any]


ExportDesc = Union[
    'FuncIdx',
    'GlobalIdx',
    'MemoryIdx',
    'TableIdx',
]


UInt8 = NewType('UInt8', int)
UInt32 = NewType('UInt32', int)

BitSize = NewType('BitSize', int)
