import pytest

from wasm.datatypes import (
    FunctionType,
    ValType,
)
from wasm.exceptions import (
    ValidationError,
)
from wasm.validation.function import (
    validate_function_type,
)


def test_validate_function_type_without_results():
    function_type = FunctionType((), ())

    validate_function_type(function_type)


def test_validate_function_type_with_single_result():
    function_type = FunctionType((), (ValType.i32,))

    validate_function_type(function_type)


def test_validate_function_type_with_multiple_results():
    function_type = FunctionType((), (ValType.i32, ValType.i32))

    with pytest.raises(ValidationError, match="Function types may only have one result"):
        validate_function_type(function_type)
