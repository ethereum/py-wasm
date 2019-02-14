from typing import (
    Iterable,
    List,
    Tuple,
    Union,
)

from wasm.datatypes import (
    LabelIdx,
    ModuleInstance,
)
from wasm.instructions import (
    BaseInstruction,
)
from wasm.stack import (
    BaseStack,
)
from wasm.typing import (
    TValue,
)

from .instructions import (
    InstructionSequence,
)


class OperandStack(BaseStack[TValue]):
    pass


TInstructions = Union[
    Tuple[BaseInstruction, ...],
    InstructionSequence,
]


class Label:
    arity: int
    instructions: InstructionSequence
    is_loop: bool
    operand_stack: OperandStack

    def __str__(self) -> str:
        return f"L(a={self.arity},loop={'yes' if self.is_loop else 'no'})"

    def __init__(self,
                 *,
                 arity: int,
                 instructions: TInstructions,
                 is_loop: bool) -> None:
        self.arity = arity
        self.is_loop = is_loop

        if isinstance(instructions, InstructionSequence):
            self.instructions = instructions
        else:
            self.instructions = InstructionSequence(instructions)

        self.operand_stack = OperandStack()


class ControlStack(BaseStack[Label]):
    def get_by_label_idx(self, key: LabelIdx) -> Label:
        return self._stack[-1 * (key + 1)]


class Frame:
    module: ModuleInstance
    locals: List[TValue]
    instructions: InstructionSequence
    arity: int

    operand_stack: OperandStack
    control_stack: ControlStack

    def __str__(self) -> str:
        return f"F(a={self.arity},locals={self.locals})"

    def __init__(self,
                 *,
                 module: ModuleInstance,
                 locals: Iterable[TValue],
                 instructions: TInstructions,
                 arity: int) -> None:
        self.module = module
        self.locals = list(locals)
        self.arity = arity

        if isinstance(instructions, InstructionSequence):
            self.instructions = instructions
        else:
            self.instructions = InstructionSequence(instructions)

        self.control_stack = ControlStack()
        self.operand_stack = OperandStack()

    @property
    def has_active_label(self) -> bool:
        return bool(self.control_stack)

    @property
    def label(self) -> Label:
        return self.control_stack.peek()

    @property
    def active_instructions(self) -> InstructionSequence:
        if self.has_active_label:
            return self.label.instructions
        else:
            return self.instructions

    @property
    def active_operand_stack(self) -> OperandStack:
        if self.has_active_label:
            return self.label.operand_stack
        else:
            return self.operand_stack


class FrameStack(BaseStack[Frame]):
    pass
