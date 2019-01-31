from wasm import (
    constants,
)
from wasm.datatypes import (
    Limits,
    Memory,
    MemoryType,
)

from .limits import (
    validate_limits,
)


def validate_memory_type(memory_type: MemoryType) -> None:
    limits = Limits(memory_type.min, memory_type.max)
    validate_limits(limits, constants.UINT16_CEIL)


def validate_memory(memory: Memory) -> None:
    validate_memory_type(memory.type)
