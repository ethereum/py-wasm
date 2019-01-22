from collections import (
    Counter,
)
from typing import (
    Iterable,
    Tuple,
    TypeVar,
)

TVal = TypeVar("TVal")


def get_duplicates(seq: Iterable[TVal]) -> Tuple[TVal, ...]:
    return tuple(
        value
        for value, count
        in Counter(seq).items()
        if count > 1
    )
