from typing import (
    Any,
    Dict,
    NewType,
)

Store = Dict[Any, Any]


UInt8 = NewType('UInt8', int)
UInt32 = NewType('UInt32', int)

BitSize = NewType('BitSize', int)
