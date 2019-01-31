from wasm import (
    constants,
)
from wasm.datatypes import (
    FunctionAddress,
    Table,
    TableType,
)
from wasm.exceptions import (
    ValidationError,
)

from .limits import (
    validate_limits,
)


def validate_table_type(table_type: TableType) -> None:
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#table-types%E2%91%A2
    """
    validate_limits(table_type.limits, constants.UINT32_CEIL)
    if table_type.elem_type is not FunctionAddress:
        raise ValidationError(
            f"TableType.elem_type must be `FunctionAddress`: Got {table_type.elem_type}"
        )


def validate_table(table: Table) -> None:
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#tables%E2%91%A2
    """
    return validate_table_type(table.type)
