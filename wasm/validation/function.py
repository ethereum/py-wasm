from wasm.datatypes import (
    FunctionType,
)
from wasm.exceptions import (
    ValidationError,
)


def validate_function_type(function_type: FunctionType) -> None:
    if len(function_type.results) > 1:
        raise ValidationError(
            f"Function types may only have one result.  Got {len(function_type.results)}"
        )
