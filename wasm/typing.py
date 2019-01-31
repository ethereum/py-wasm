from typing import (
    Any,
    Callable,
    Dict,
    List,
    NewType,
    Tuple,
    Union,
)

Store = Dict[Any, Any]
HostFunctionCallable = Callable[[Store, List[Any]], Tuple[Store, Any]]


UInt8 = NewType('UInt8', int)
UInt32 = NewType('UInt32', int)
UInt64 = NewType('UInt64', int)


SInt32 = NewType('SInt32', int)
SInt64 = NewType('SInt64', int)


Float32 = NewType('Float32', float)
Float64 = NewType('Float64', float)


TValue = Union[
    UInt32,
    UInt64,
    Float32,
    Float64,
]
