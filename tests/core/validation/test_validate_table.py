import pytest

from wasm.datatypes import (
    FunctionAddress,
    Limits,
    Table,
    TableType,
)
from wasm.exceptions import (
    ValidationError,
)
from wasm.validation import (
    validate_table,
)


def test_validate_table_success():
    table = Table(TableType(Limits(0, 100), FunctionAddress))

    validate_table(table)


@pytest.mark.parametrize(
    'table_type,match',
    (
        (TableType(Limits(10, 9), FunctionAddress), 'Limits'),
        (TableType(Limits(0, 100), None), 'FunctionAddress'),
    )
)
def test_validate_table_type_failures(table_type, match):
    table = Table(table_type)

    with pytest.raises(ValidationError, match=match):
        validate_table(table)
