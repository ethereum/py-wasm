import io
from typing import (
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


def parse_table_element_type(stream: io.BytesIO) -> Type[FunctionAddress]:
    type_flag = parse_single_byte(stream)

    if type_flag == 0x70:
        return FunctionAddress
    else:
        raise MalformedModule(
            f"Unrecognized table element type: {hex(type_flag)}"
        )


def parse_table_type(stream: io.BytesIO) -> TableType:
    element_type = parse_table_element_type(stream)
    limits = parse_limits(stream)
    return TableType(limits, element_type)


def parse_table(stream: io.BytesIO) -> Table:
    table_type = parse_table_type(stream)
    return Table(table_type)
