from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Tuple,
)

from wasm.datatypes import (
    LabelIdx,
    Store,
)
from wasm.typing import (
    TValue,
)

from .instructions import (
    InstructionSequence,
)
from .stack import (
    Frame,
    FrameStack,
    Label,
    OperandStack,
)


class BaseConfiguration(ABC):
    store: Store

    def __init__(self, store: Store) -> None:
        self.store = store
        self.result_stack = OperandStack()

    @property
    @abstractmethod
    def frame(self) -> Frame:
        pass

    @property
    @abstractmethod
    def has_active_frame(self) -> bool:
        pass

    @property
    @abstractmethod
    def has_active_label(self) -> bool:
        pass

    @property
    @abstractmethod
    def active_label(self) -> Label:
        pass

    @property
    @abstractmethod
    def instructions(self) -> InstructionSequence:
        pass

    #
    # Operands
    #
    @property
    @abstractmethod
    def operand_stack_size(self) -> int:
        pass

    @abstractmethod
    def push_operand(self, value: TValue) -> None:
        pass

    @abstractmethod
    def pop_operand(self) -> TValue:
        pass

    @abstractmethod
    def pop2_operands(self) -> Tuple[TValue, TValue]:
        pass

    @abstractmethod
    def pop3_operands(self) -> Tuple[TValue, TValue, TValue]:
        pass

    #
    # Frames
    #
    @property
    @abstractmethod
    def frame_stack_size(self) -> int:
        pass

    @abstractmethod
    def push_frame(self, frame: Frame) -> None:
        pass

    @abstractmethod
    def pop_frame(self) -> Frame:
        pass

    #
    # Labels
    #
    @property
    @abstractmethod
    def label_stack_size(self) -> int:
        pass

    @abstractmethod
    def push_label(self, label: Label) -> None:
        pass

    @abstractmethod
    def pop_label(self) -> Label:
        pass

    @abstractmethod
    def get_by_label_idx(self, key: LabelIdx) -> Label:
        pass


class Configuration(BaseConfiguration):
    frame_stack: FrameStack

    def __init__(self, store: Store) -> None:
        super().__init__(store)
        self.frame_stack = FrameStack()

    @property
    def frame(self) -> Frame:
        return self.frame_stack.peek()

    @property
    def has_active_frame(self) -> bool:
        return bool(self.frame_stack)

    @property
    def active_label(self) -> Label:
        return self.frame.control_stack.peek()

    @property
    def has_active_label(self) -> bool:
        if not self.has_active_frame:
            return False
        return bool(self.frame.control_stack)

    @property
    def instructions(self) -> InstructionSequence:
        return self.frame.active_instructions

    #
    # Operands
    #
    @property
    def operand_stack_size(self) -> int:
        return len(self.frame.active_operand_stack)

    def push_operand(self, value: TValue) -> None:
        self.frame.active_operand_stack.push(value)

    def pop_operand(self) -> TValue:
        return self.frame.active_operand_stack.pop()

    def pop2_operands(self) -> Tuple[TValue, TValue]:
        return self.frame.active_operand_stack.pop2()

    def pop3_operands(self) -> Tuple[TValue, TValue, TValue]:
        return self.frame.active_operand_stack.pop3()

    #
    # Frames
    #
    @property
    def frame_stack_size(self) -> int:
        return len(self.frame_stack)

    def push_frame(self, frame: Frame) -> None:
        self.frame_stack.push(frame)

    def pop_frame(self) -> Frame:
        return self.frame_stack.pop()

    #
    # Labels
    #
    @property
    def label_stack_size(self) -> int:
        return len(self.frame.control_stack)

    def push_label(self, label: Label) -> None:
        self.frame.control_stack.push(label)

    def pop_label(self) -> Label:
        return self.frame.control_stack.pop()

    def get_by_label_idx(self, key: LabelIdx) -> Label:
        return self.frame.control_stack.get_by_label_idx(key)
