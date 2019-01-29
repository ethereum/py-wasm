from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    NewType,
    Tuple,
    Union,
)

if TYPE_CHECKING:
    from wasm.instructions import (  # noqa: F401
        Instruction,
    )
    from wasm.datatypes import (  # noqa: F401
        FuncIdx,
        FunctionType,
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
Config = Dict[Any, Any]


Expression = Tuple["Instruction", ...]


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
    'FunctionType',
    'TableType',
    'MemoryType',
    'GlobalType',
]


UInt8 = NewType('UInt8', int)
UInt32 = NewType('UInt32', int)
UInt64 = NewType('UInt64', int)


SInt32 = NewType('SInt32', int)
SInt64 = NewType('SInt64', int)


Float32 = NewType('Float32', float)
Float64 = NewType('Float64', float)
