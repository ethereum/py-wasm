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
    """
    Base class for the various Stack implementations.
    """
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
        """
        Pop a single value off the top of the stack.

        Raise an IndexError if the stack is empty
        """
        return self._stack.pop()

    def pop2(self) -> Tuple[TStackItem, TStackItem]:
        """
        Pop two values off the top of the stack.

        Raise an IndexError if there are insufficient values on the stack.
        """
        return self._stack.pop(), self._stack.pop()

    def pop3(self) -> Tuple[TStackItem, TStackItem, TStackItem]:
        """
        Pop three values off the top of the stack.

        Raise an IndexError if there are insufficient values on the stack.
        """
        return self._stack.pop(), self._stack.pop(), self._stack.pop()

    def push(self, value: TStackItem) -> None:
        """
        Push a single value onto the stack.
        """
        self._stack.append(value)

    def peek(self) -> TStackItem:
        """
        Return the value on top of the stack.

        Raise an IndexError if the stack is empty
        """
        return self._stack[-1]

    def extend(self, values: Iterable[TStackItem]) -> None:
        """
        Extend the stack with the iterable of values.
        """
        self._stack.extend(values)
