from typing import (
    IO,
    Union,
)

from wasm.datatypes import (
    GlobalType,
    Import,
    MemoryType,
    TableType,
    TypeIdx,
)
from wasm.exceptions import (
    MalformedModule,
)

from .byte import (
    parse_single_byte,
)
from .globals import (
    parse_global_type,
)
from .indices import (
    parse_type_idx,
)
from .memory import (
    parse_memory_type,
)
from .tables import (
    parse_table_type,
)
from .text import (
    parse_text,
)

TImportDesc = Union[TypeIdx, GlobalType, MemoryType, TableType]


def parse_import_descriptor(stream: IO[bytes]) -> TImportDesc:
    type_flag = parse_single_byte(stream)

    if type_flag == 0x00:
        return parse_type_idx(stream)
    elif type_flag == 0x01:
        return parse_table_type(stream)
    elif type_flag == 0x02:
        return parse_memory_type(stream)
    elif type_flag == 0x03:
        return parse_global_type(stream)
    else:
        raise MalformedModule(
            f"Unknown leading byte for import descriptor: {hex(type_flag)}"
        )


def parse_import(stream: IO[bytes]) -> Import:
    module_name = parse_text(stream)
    as_name = parse_text(stream)
    descriptor = parse_import_descriptor(stream)
    return Import(module_name, as_name, descriptor)
