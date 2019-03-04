from wasm.datatypes import (
    LabelIdx,
)
from wasm.exceptions import (
    ValidationError,
)
from wasm.stack import (
    BaseStack,
)

from .control_frame import (
    ControlFrame,
)
from .operand import (
    Operand,
)


class ControlStack(BaseStack[ControlFrame]):
    """
    Stack used during expression validation for control frames
    """
    def get_label_by_idx(self, key: LabelIdx) -> ControlFrame:
        return self._stack[-1 * (key + 1)]

    def validate_label_idx(self, label_idx: LabelIdx) -> None:
        if label_idx >= len(self):
            raise ValidationError(
                "Label index exceeds number of available control frames: "
                f"{label_idx} > {len(self)}"
            )


class OperandStack(BaseStack[Operand]):
    """
    Stack used during expression validation for operands
    """
    pass
