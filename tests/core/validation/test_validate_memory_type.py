import pytest

from wasm.datatypes import (
    MemoryType,
)
from wasm.exceptions import (
    ValidationError,
)
from wasm.validation import (
    validate_memory_type,
)


def test_validate_memory_type_success():
    memory_type = MemoryType(0, 2**16)

    validate_memory_type(memory_type)


def test_validate_memory_type_failure():
    memory_type = MemoryType(0, 2**16 + 1)

    with pytest.raises(ValidationError, match="Limits.max exceeds upper bound"):
        validate_memory_type(memory_type)
