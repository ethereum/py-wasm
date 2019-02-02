import pytest

from wasm.datatypes import (
    Memory,
    MemoryType,
)
from wasm.exceptions import (
    ValidationError,
)
from wasm.validation import (
    validate_memory,
)


def test_validate_memory_success():
    memory = Memory(MemoryType(0, 2**16))

    validate_memory(memory)


def test_validate_memory_failure():
    memory = Memory(MemoryType(0, 2**16 + 1))

    with pytest.raises(ValidationError, match="Limits.max exceeds upper bound"):
        validate_memory(memory)
