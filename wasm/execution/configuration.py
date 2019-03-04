from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Iterable,
    List,
    Tuple,
    cast,
)

import numpy

from wasm.datatypes import (
    LabelIdx,
    ModuleInstance,
    Store,
)
from wasm.exceptions import (
    Exhaustion,
)
from wasm.instructions import (
    BaseInstruction,
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
    """
    Base class for the Configuration object used for execution Web Assembly
    """
    store: Store
    current_instruction: BaseInstruction

    def __init__(self, store: Store) -> None:
        self.store = store
        self.result_stack = OperandStack()

    @abstractmethod
    def execute(self) -> Tuple[TValue, ...]:
        pass

    @abstractmethod
    def seek_to_instruction_idx(self, index: int) -> None:
        pass

    @property
    @abstractmethod
    def has_active_frame(self) -> bool:
        pass

    @property
    @abstractmethod
    def frame_arity(self) -> int:
        pass

    @property
    @abstractmethod
    def frame_locals(self) -> List[TValue]:
        pass

    @property
    @abstractmethod
    def frame_module(self) -> ModuleInstance:
        pass

    @property
    @abstractmethod
    def has_active_label(self) -> bool:
        pass

    @property
    @abstractmethod
    def active_label(self) -> Label:
        pass

    #
    # Results
    #
    @abstractmethod
    def push_result(self, value: TValue) -> None:
        pass

    @abstractmethod
    def extend_results(self, values: Iterable[TValue]) -> None:
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
    def extend_operands(self, values: Iterable[TValue]) -> None:
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
    # Pop u32
    #
    @abstractmethod
    def pop_u32(self) -> numpy.uint32:
        pass

    @abstractmethod
    def pop2_u32(self) -> Tuple[numpy.uint32, numpy.uint32]:
        pass

    @abstractmethod
    def pop3_u32(self) -> Tuple[numpy.uint32, numpy.uint32, numpy.uint32]:
        pass

    #
    # Pop u64
    #
    @abstractmethod
    def pop_u64(self) -> numpy.uint64:
        pass

    @abstractmethod
    def pop2_u64(self) -> Tuple[numpy.uint64, numpy.uint64]:
        pass

    @abstractmethod
    def pop3_u64(self) -> Tuple[numpy.uint64, numpy.uint64, numpy.uint64]:
        pass

    #
    # Pop f32
    #
    @abstractmethod
    def pop_f32(self) -> numpy.float32:
        pass

    @abstractmethod
    def pop2_f32(self) -> Tuple[numpy.float32, numpy.float32]:
        pass

    @abstractmethod
    def pop3_f32(self) -> Tuple[numpy.float32, numpy.float32, numpy.float32]:
        pass

    #
    # Pop f64
    #
    @abstractmethod
    def pop_f64(self) -> numpy.float64:
        pass

    @abstractmethod
    def pop2_f64(self) -> Tuple[numpy.float64, numpy.float64]:
        pass

    @abstractmethod
    def pop3_f64(self) -> Tuple[numpy.float64, numpy.float64, numpy.float64]:
        pass

    #
    # Frames
    #
    @abstractmethod
    def push_frame(self, frame: Frame) -> None:
        pass

    @abstractmethod
    def pop_frame(self) -> Frame:
        pass

    #
    # Labels
    #
    @abstractmethod
    def push_label(self, label: Label) -> None:
        pass

    @abstractmethod
    def pop_label(self) -> Label:
        pass

    @abstractmethod
    def get_label_by_idx(self, key: LabelIdx) -> Label:
        pass


class Configuration(BaseConfiguration):
    """
    An implementation of the configuration API that uses separate stacks for
    frames, labels, and operands.
    """
    _frame_stack: FrameStack
    _frame: Frame
    _instructions: InstructionSequence
    _operand_stack: OperandStack

    def __init__(self, store: Store) -> None:
        super().__init__(store)
        self._frame_stack = FrameStack()

    def execute(self) -> Tuple[TValue, ...]:
        from wasm.logic import OPCODE_TO_LOGIC_FN

        while True:
            # This loop has been written the following way for performance
            # reasons and should not be optimized for readability without
            # taking performance into account.
            #
            # 1. Use of direct call to `instructions.__next__()` to avoid extra
            #    call frame of using `next` builtin
            # 2. Catching `AttributeError` on access to `self.instructions` to
            #    avoid extra cost of checking if the attribute is present.
            try:
                instructions = self._instructions
            except AttributeError:
                del self.current_instruction
                break

            self.current_instruction = instructions.__next__()

            logic_fn = OPCODE_TO_LOGIC_FN[self.current_instruction.opcode]

            logic_fn(self)

        if len(self.result_stack) > 1:
            raise Exception("Invariant: The WASM spec only allows singular return values.")
        elif len(self.result_stack) == 1:
            return (self.result_stack.pop(),)
        else:
            return tuple()

    def seek_to_instruction_idx(self, index: int) -> None:
        self._instructions.seek(index)

    @property
    def has_active_frame(self) -> bool:
        try:
            return bool(self._frame)
        except AttributeError:
            return False

    @property
    def frame_arity(self) -> int:
        return self._frame.arity

    @property
    def frame_locals(self) -> List[TValue]:
        return self._frame.locals

    @property
    def frame_module(self) -> ModuleInstance:
        return self._frame.module

    @property
    def active_label(self) -> Label:
        return self._frame.label

    @property
    def has_active_label(self) -> bool:
        try:
            return bool(self._frame.label)
        except AttributeError:
            return False

    #
    # Results
    #
    def push_result(self, value: TValue) -> None:
        self.result_stack.push(value)

    def extend_results(self, values: Iterable[TValue]) -> None:
        self.result_stack.extend(values)

    #
    # Operands
    #
    @property
    def operand_stack_size(self) -> int:
        return len(self._operand_stack)

    def push_operand(self, value: TValue) -> None:
        self._operand_stack.push(value)

    def extend_operands(self, values: Iterable[TValue]) -> None:
        self._operand_stack.extend(values)

    def pop_operand(self) -> TValue:
        return self._operand_stack.pop()

    def pop2_operands(self) -> Tuple[TValue, TValue]:
        return self._operand_stack.pop2()

    def pop3_operands(self) -> Tuple[TValue, TValue, TValue]:
        return self._operand_stack.pop3()

    #
    # Pop u32
    #
    def pop_u32(self) -> numpy.uint32:
        return cast(numpy.uint32, self._operand_stack.pop())

    def pop2_u32(self) -> Tuple[numpy.uint32, numpy.uint32]:
        a, b = self._operand_stack.pop2()
        return cast(numpy.uint32, a), cast(numpy.uint32, b)

    def pop3_u32(self) -> Tuple[numpy.uint32, numpy.uint32, numpy.uint32]:
        a, b, c = self._operand_stack.pop3()
        return cast(numpy.uint32, a), cast(numpy.uint32, b), cast(numpy.uint32, c)

    #
    # Pop u64
    #
    def pop_u64(self) -> numpy.uint64:
        return cast(numpy.uint64, self._operand_stack.pop())

    def pop2_u64(self) -> Tuple[numpy.uint64, numpy.uint64]:
        a, b = self._operand_stack.pop2()
        return cast(numpy.uint64, a), cast(numpy.uint64, b)

    def pop3_u64(self) -> Tuple[numpy.uint64, numpy.uint64, numpy.uint64]:
        a, b, c = self._operand_stack.pop3()
        return cast(numpy.uint64, a), cast(numpy.uint64, b), cast(numpy.uint64, c)

    #
    # Pop f32
    #
    def pop_f32(self) -> numpy.float32:
        return cast(numpy.float32, self._operand_stack.pop())

    def pop2_f32(self) -> Tuple[numpy.float32, numpy.float32]:
        a, b = self._operand_stack.pop2()
        return cast(numpy.float32, a), cast(numpy.float32, b)

    def pop3_f32(self) -> Tuple[numpy.float32, numpy.float32, numpy.float32]:
        a, b, c = self._operand_stack.pop3()
        return cast(numpy.float32, a), cast(numpy.float32, b), cast(numpy.float32, c)

    #
    # Pop f64
    #
    def pop_f64(self) -> numpy.float64:
        return cast(numpy.float64, self._operand_stack.pop())

    def pop2_f64(self) -> Tuple[numpy.float64, numpy.float64]:
        a, b = self._operand_stack.pop2()
        return cast(numpy.float64, a), cast(numpy.float64, b)

    def pop3_f64(self) -> Tuple[numpy.float64, numpy.float64, numpy.float64]:
        a, b, c = self._operand_stack.pop3()
        return cast(numpy.float64, a), cast(numpy.float64, b), cast(numpy.float64, c)

    #
    # Frames
    #
    def push_frame(self, frame: Frame) -> None:
        if len(self._frame_stack) > 1024:
            # This is not part of spec, but this is required to pass tests.
            # Tests pass with limit 10000, maybe more
            raise Exhaustion("Too many call frames.  Cannot exceed 1024")

        self._frame = frame
        self._frame_stack.push(frame)
        self._operand_stack = self._frame.active_operand_stack
        self._instructions = frame.active_instructions

    def pop_frame(self) -> Frame:
        if self.has_active_label:
            raise ValueError("Cannot pop frame while there is an active label")
        frame = self._frame_stack.pop()
        try:
            self._frame = self._frame_stack.peek()
            self._operand_stack = self._frame.active_operand_stack
            self._instructions = self._frame.active_instructions
        except IndexError:
            del self._frame
            del self._operand_stack
            del self._instructions

        return frame

    #
    # Labels
    #
    def push_label(self, label: Label) -> None:
        self._frame.push_label(label)
        self._operand_stack = label.operand_stack
        self._instructions = label.instructions

    def pop_label(self) -> Label:
        label = self._frame.pop_label()
        self._operand_stack = self._frame.active_operand_stack
        self._instructions = self._frame.active_instructions
        return label

    def get_label_by_idx(self, key: LabelIdx) -> Label:
        return self._frame.control_stack.get_label_by_idx(key)
