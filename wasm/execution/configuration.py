from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Iterable,
    Tuple,
    cast,
)

from wasm.datatypes import (
    LabelIdx,
    Store,
)
from wasm.typing import (
    Float32,
    Float64,
    TValue,
    UInt32,
    UInt64,
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

    @abstractmethod
    def execute(self) -> Tuple[TValue, ...]:
        pass

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
    def pop_u32(self) -> UInt32:
        pass

    @abstractmethod
    def pop2_u32(self) -> Tuple[UInt32, UInt32]:
        pass

    @abstractmethod
    def pop3_u32(self) -> Tuple[UInt32, UInt32, UInt32]:
        pass

    #
    # Pop u64
    #
    def pop_u64(self) -> UInt64:
        return cast(UInt64, self.frame.active_operand_stack.pop())

    def pop2_u64(self) -> Tuple[UInt64, UInt64]:
        a, b = self.frame.active_operand_stack.pop2()
        return cast(UInt64, a), cast(UInt64, b)

    def pop3_u64(self) -> Tuple[UInt64, UInt64, UInt64]:
        a, b, c = self.frame.active_operand_stack.pop3()
        return cast(UInt64, a), cast(UInt64, b), cast(UInt64, c)

    #
    # Pop f32
    #
    @abstractmethod
    def pop_f32(self) -> Float32:
        pass

    @abstractmethod
    def pop2_f32(self) -> Tuple[Float32, Float32]:
        pass

    @abstractmethod
    def pop3_f32(self) -> Tuple[Float32, Float32, Float32]:
        pass

    #
    # Pop f64
    #
    @abstractmethod
    def pop_f64(self) -> Float64:
        pass

    @abstractmethod
    def pop2_f64(self) -> Tuple[Float64, Float64]:
        pass

    @abstractmethod
    def pop3_f64(self) -> Tuple[Float64, Float64, Float64]:
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

    def execute(self) -> Tuple[TValue, ...]:
        # TODO: unwrap import once logic functions move out of wasm.main
        from wasm.main import opcode2exec
        from wasm.logic import OPCODE_TO_LOGIC_FN

        while self.has_active_frame:
            instruction = next(self.instructions)

            if instruction.opcode in OPCODE_TO_LOGIC_FN:
                assert instruction.opcode not in opcode2exec
                logic_fn = OPCODE_TO_LOGIC_FN[instruction.opcode]
            else:
                logic_fn = opcode2exec[instruction.opcode][0]

            logic_fn(self)

        if len(self.result_stack) > 1:
            raise Exception("Invariant: The WASM spec only allows singular return values.")
        elif len(self.result_stack) == 1:
            return (self.result_stack.pop(),)
        else:
            return tuple()

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
        return len(self.frame.active_operand_stack)

    def push_operand(self, value: TValue) -> None:
        self.frame.active_operand_stack.push(value)

    def extend_operands(self, values: Iterable[TValue]) -> None:
        self.frame.active_operand_stack.extend(values)

    def pop_operand(self) -> TValue:
        return self.frame.active_operand_stack.pop()

    def pop2_operands(self) -> Tuple[TValue, TValue]:
        return self.frame.active_operand_stack.pop2()

    def pop3_operands(self) -> Tuple[TValue, TValue, TValue]:
        return self.frame.active_operand_stack.pop3()

    #
    # Pop u32
    #
    def pop_u32(self) -> UInt32:
        return cast(UInt32, self.frame.active_operand_stack.pop())

    def pop2_u32(self) -> Tuple[UInt32, UInt32]:
        a, b = self.frame.active_operand_stack.pop2()
        return cast(UInt32, a), cast(UInt32, b)

    def pop3_u32(self) -> Tuple[UInt32, UInt32, UInt32]:
        a, b, c = self.frame.active_operand_stack.pop3()
        return cast(UInt32, a), cast(UInt32, b), cast(UInt32, c)

    #
    # Pop u64
    #
    def pop_u64(self) -> UInt64:
        return cast(UInt64, self.frame.active_operand_stack.pop())

    def pop2_u64(self) -> Tuple[UInt64, UInt64]:
        a, b = self.frame.active_operand_stack.pop2()
        return cast(UInt64, a), cast(UInt64, b)

    def pop3_u64(self) -> Tuple[UInt64, UInt64, UInt64]:
        a, b, c = self.frame.active_operand_stack.pop3()
        return cast(UInt64, a), cast(UInt64, b), cast(UInt64, c)

    #
    # Pop f32
    #
    def pop_f32(self) -> Float32:
        return cast(Float32, self.frame.active_operand_stack.pop())

    def pop2_f32(self) -> Tuple[Float32, Float32]:
        a, b = self.frame.active_operand_stack.pop2()
        return cast(Float32, a), cast(Float32, b)

    def pop3_f32(self) -> Tuple[Float32, Float32, Float32]:
        a, b, c = self.frame.active_operand_stack.pop3()
        return cast(Float32, a), cast(Float32, b), cast(Float32, c)

    #
    # Pop f64
    #
    def pop_f64(self) -> Float64:
        return cast(Float64, self.frame.active_operand_stack.pop())

    def pop2_f64(self) -> Tuple[Float64, Float64]:
        a, b = self.frame.active_operand_stack.pop2()
        return cast(Float64, a), cast(Float64, b)

    def pop3_f64(self) -> Tuple[Float64, Float64, Float64]:
        a, b, c = self.frame.active_operand_stack.pop3()
        return cast(Float64, a), cast(Float64, b), cast(Float64, c)

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
