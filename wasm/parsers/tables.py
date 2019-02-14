from typing import (
    IO,
    Type,
)

from wasm.datatypes import (
    FunctionAddress,
    Table,
    TableType,
)
from wasm.exceptions import (
    MalformedModule,
)

from .byte import (
    parse_single_byte,
)
from .limits import (
    parse_limits,
)


def parse_table_element_type(stream: IO[bytes]) -> Type[FunctionAddress]:
    """
    Parse the element type for a TableType
    """
    type_flag = parse_single_byte(stream)

    if type_flag == 0x70:
        return FunctionAddress
    else:
        raise MalformedModule(
            f"Unrecognized table element type: {hex(type_flag)}"
        )


def parse_table_type(stream: IO[bytes]) -> TableType:
    """
    Parser for the TableType type
    """
    element_type = parse_table_element_type(stream)
    limits = parse_limits(stream)
    return TableType(limits, element_type)


def parse_table(stream: IO[bytes]) -> Table:
    """
    Parser for the Table type
    """
    table_type = parse_table_type(stream)
    return Table(table_type)
