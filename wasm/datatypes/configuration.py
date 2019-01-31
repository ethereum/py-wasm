from typing import (
    NamedTuple,
)

from .instructions import (
    InstructionSequence,
)
from .stack import (
    Frame,
    FrameStack,
    Label,
    LabelStack,
    ValueStack,
)
from .store import (
    Store,
)


class Configuration(NamedTuple):
    store: Store
    value_stack: ValueStack
    label_stack: LabelStack
    frame_stack: FrameStack

    @property
    def frame(self) -> Frame:
        return self.frame_stack.peek()

    @property
    def has_active_frame(self):
        return bool(self.frame_stack)

    @property
    def label(self) -> Label:
        if self.has_active_frame and self.has_active_label:
            return self.label_stack.peek()
        else:
            raise IndexError("No labels active for current frame")

    @property
    def has_active_label(self):
        if not self.has_active_frame:
            return False
        elif not self.label_stack:
            return False
        else:
            return self.label_stack.peek().frame_id == self.frame.id

    @property
    def instructions(self) -> InstructionSequence:
        if self.has_active_label:
            return self.label.instructions
        elif len(self.frame_stack):
            return self.frame_stack.peek().instructions
        else:
            raise ValueError("No active instructions")

    @property
    def is_executable(self) -> bool:
        return self.has_active_frame
