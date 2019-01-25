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
        FuncType,
        GlobalIdx,
        GlobalType,
        MemoryIdx,
        MemoryType,
        TableIdx,
        TableType,
        TypeIdx,
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


ImportDesc = Union[
    'TypeIdx',
    'TableType',
    'MemoryType',
    'GlobalType',
]


ExternType = Union[
    'FuncType',
    'TableType',
    'MemoryType',
    'GlobalType',
]


UInt8 = NewType('UInt8', int)
UInt32 = NewType('UInt32', int)
