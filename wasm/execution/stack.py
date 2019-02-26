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
    """
    A stack used for operands during Web Assembly execution
    """
    pass


TInstructions = Union[
    Tuple[BaseInstruction, ...],
    InstructionSequence,
]


class Label:
    """
    A label object used during Web Asembly execution
    """
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
    """
    A stack used for labels during Web Assembly execution
    """
    def get_by_label_idx(self, key: LabelIdx) -> Label:
        return self._stack[-1 * (key + 1)]


class Frame:
    """
    A frame object used during Web Asembly execution
    """
    module: ModuleInstance
    locals: List[TValue]
    instructions: InstructionSequence
    active_instructions: InstructionSequence
    active_operand_stack: OperandStack
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

        self.active_instructions = self.instructions
        self.active_operand_stack = self.operand_stack

    def push_label(self, label: Label) -> None:
        self.control_stack.push(label)
        self.active_instructions = label.instructions
        self.active_operand_stack = label.operand_stack

    def pop_label(self) -> Label:
        label = self.control_stack.pop()
        if self.control_stack:
            active_label = self.control_stack.peek()
            self.active_instructions = active_label.instructions
            self.active_operand_stack = active_label.operand_stack
        else:
            self.active_instructions = self.instructions
            self.active_operand_stack = self.operand_stack
        return label

    @property
    def has_active_label(self) -> bool:
        return bool(self.control_stack)

    @property
    def label(self) -> Label:
        return self.control_stack.peek()


class FrameStack(BaseStack[Frame]):
    """
    A stack used for frames during Web Assembly execution
    """
    pass
