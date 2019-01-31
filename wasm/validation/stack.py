from wasm.datatypes import (
    BaseStack,
    LabelIdx,
)
from wasm.exceptions import (
    ValidationError,
)

from .control_frame import (
    ControlFrame,
)
from .operand import (
    Operand,
)


class ControlStack(BaseStack[ControlFrame]):
    def get_by_label_idx(self, key: LabelIdx) -> ControlFrame:
        return self._stack[-1 * (key + 1)]

    def validate_label_idx(self, label_idx: LabelIdx) -> None:
        if label_idx >= len(self):
            raise ValidationError(
                "Label index exceeds number of available control frames: "
                f"{label_idx} > {len(self)}"
            )


class OperandStack(BaseStack[Operand]):
    pass
