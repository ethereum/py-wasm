from collections.abc import (
    Sequence,
)
from typing import (
    Generic,
    Iterable,
    Iterator,
    List,
    Tuple,
    TypeVar,
    overload,
)

TStackItem = TypeVar('TStackItem')


class BaseStack(Sequence, Generic[TStackItem]):
    _stack: List[TStackItem]

    def __init__(self) -> None:
        self._stack = []

    def __len__(self) -> int:
        return len(self._stack)

    def __bool__(self) -> bool:
        return bool(self._stack)

    def __iter__(self) -> Iterator[TStackItem]:
        return iter(self._stack)

    @overload
    def __getitem__(self, idx: int) -> TStackItem:
        pass

    @overload  # noqa: 811
    def __getitem__(self, s: slice) -> 'Sequence[TStackItem]':
        pass

    def __getitem__(self, item):  # noqa: F811
        if isinstance(item, int):
            return self._instructions[item]
        elif isinstance(item, slice):
            return self._instructions[item]
        else:
            raise TypeError(f"Unsupported key type: {type(item)}")

    def pop(self) -> TStackItem:
        return self._stack.pop()

    def pop2(self) -> Tuple[TStackItem, TStackItem]:
        return self._stack.pop(), self._stack.pop()

    def pop3(self) -> Tuple[TStackItem, TStackItem, TStackItem]:
        return self._stack.pop(), self._stack.pop(), self._stack.pop()

    def push(self, value: TStackItem) -> None:
        self._stack.append(value)

    def peek(self) -> TStackItem:
        return self._stack[-1]

    def extend(self, values: Iterable[TStackItem]) -> None:
        self._stack.extend(values)
