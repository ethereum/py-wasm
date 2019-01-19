from collections import (
    Counter,
)
from typing import (
    Sequence,
    Tuple,
    TypeVar,
)

TVal = TypeVar("TVal")


def get_duplicates(seq: Sequence[TVal]) -> Tuple[TVal, ...]:
    return tuple(
        value
        for value, count
        in Counter(seq).items()
        if count > 1
    )
