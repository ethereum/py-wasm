from typing import (
    NamedTuple,
    Tuple,
)

from wasm.datatypes import (
    ValType,
)


class ControlFrame(NamedTuple):
    """
    Represents the equivalent of a label during expression validation.
    """
    label_types: Tuple[ValType, ...]
    end_types: Tuple[ValType, ...]
    height: int
    is_unreachable: bool

    def mark_unreachable(self) -> 'ControlFrame':
        """
        Recurn a copy of `self` with the `is_unreachable` flag set.
        """
        return type(self)(
            self.label_types,
            self.end_types,
            self.height,
            True,
        )
