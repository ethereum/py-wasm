import pytest

from wasm.datatypes import (
    FunctionAddress,
    Limits,
    TableType,
)
from wasm.exceptions import (
    ValidationError,
)
from wasm.validation.tables import (
    validate_table_type,
)


def test_validate_table_type_success():
    table_type = TableType(Limits(0, 100), FunctionAddress)

    validate_table_type(table_type)


@pytest.mark.parametrize(
    'table_type,match',
    (
        (TableType(Limits(10, 9), FunctionAddress), 'Limits'),
        (TableType(Limits(0, 100), None), 'FunctionAddress'),
    )
)
def test_validate_table_type_failures(table_type, match):

    with pytest.raises(ValidationError, match=match):
        validate_table_type(table_type)
