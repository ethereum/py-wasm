from typing import (
    Any,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from mypy_extensions import (
    TypedDict,
)

T = TypeVar('T')


class TErrorOptions(TypedDict):
    all: str
    divide: str
    over: str
    under: str
    invalid: str


def seterr(all: str = None,
           divide: str = None,
           over: str = None,
           under: str = None,
           invalid: str = None) -> TErrorOptions:
    ...


class __base_dtype:
    def tobytes(self) -> bytes:
        ...

    def __add__(self, other: T) -> T:
        ...

    def __sub__(self, other: T) -> T:
        ...

    def __mul__(self, other: T) -> T:
        ...

    def __floordiv__(self, other: T) -> T:
        ...

    def __truediv__(self, other: T) -> T:
        ...


class __dint(__base_dtype):
    def __mod__(self, other: T) -> T:
        ...

    def __or__(self, other: T) -> T:
        ...

    def __xor__(self, other: T) -> T:
        ...

    def __and__(self, other: T) -> T:
        ...

    def __lshift__(self) -> T:
        ...

    def __rshift__(self) -> T:
        ...


class int8(__dint, int):
    ...


class int16(__dint, int):
    ...


class int32(__dint, int):
    ...


class int64(__dint, int):
    ...


class uint8(__dint, int):
    ...


class uint16(__dint, int):
    ...


class uint32(__dint, int):
    ...


class uint64(__dint, int):
    ...


class float32(__base_dtype, float):
    ...


class float64(__base_dtype, float):
    ...


TValue = Union[
    int8,
    int16,
    int32,
    int64,
    uint8,
    uint16,
    uint32,
    uint64,
    float32,
    float64,
]

TUnsignedInteger = Union[
    uint8,
    uint16,
    uint32,
    uint64,
]


inf: float = ...
nan: float = ...


def frombuffer(buffer: bytes, type_: Type[T]) -> Tuple[T, ...]:
    ...


def isinf(v: Any) -> bool:
    ...


def isposinf(v: Any) -> bool:
    ...


def isneginf(v: Any) -> bool:
    ...


def isnan(v: Any) -> bool:
    ...


def abs(v: T) -> T:
    ...


def ceil(v: T) -> T:
    ...


def floor(v: T) -> T:
    ...


def trunc(v: T) -> T:
    ...


def round(v: T) -> T:
    ...


def sqrt(v: T) -> T:
    ...
