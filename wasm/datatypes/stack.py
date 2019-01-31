from typing import (
    Generic,
    Iterable,
    List,
    NamedTuple,
    Tuple,
    TypeVar,
)
import uuid

from wasm.typing import (
    TValue,
)

from .indices import (
    LabelIdx,
)
from .instructions import (
    InstructionSequence,
)
from .module import (
    ModuleInstance,
)

TStackItem = TypeVar('TStackItem')


class BaseStack(Generic[TStackItem]):
    _stack: List[TStackItem]

    def __init__(self) -> None:
        self._stack = []

    def __len__(self) -> int:
        return len(self._stack)

    def __bool__(self) -> bool:
        return bool(self._stack)

    def __iter__(self) -> Iterable[TStackItem]:
        return iter(self._stack)

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


class ValueStack(BaseStack[TValue]):
    pass


class Frame(NamedTuple):
    id: uuid.UUID
    module: ModuleInstance
    locals: List[TValue]
    instructions: InstructionSequence
    arity: int
    height: int


class FrameStack(BaseStack[Frame]):
    pass


class Label(NamedTuple):
    arity: int
    height: int
    instructions: InstructionSequence
    is_loop: bool
    frame_id: uuid.UUID


class LabelStack(BaseStack[Label]):
    def get_by_label_idx(self, key: LabelIdx) -> Label:
        return self._stack[-1 * (key + 1)]
