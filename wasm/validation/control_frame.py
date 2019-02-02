from typing import (
    NamedTuple,
    Tuple,
)

from wasm.datatypes import (
    ValType,
)


class ControlFrame(NamedTuple):
    label_types: Tuple[ValType, ...]
    end_types: Tuple[ValType, ...]
    height: int
    is_unreachable: bool

    def mark_unreachable(self) -> 'ControlFrame':
        return type(self)(
            self.label_types,
            self.end_types,
            self.height,
            True,
        )
