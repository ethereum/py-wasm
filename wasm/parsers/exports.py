from typing import (
    IO,
    Union,
)

from wasm.datatypes import (
    Export,
    FunctionIdx,
    GlobalIdx,
    MemoryIdx,
    TableIdx,
)
from wasm.exceptions import (
    MalformedModule,
)

from .byte import (
    parse_single_byte,
)
from .indices import (
    parse_function_idx,
    parse_global_idx,
    parse_memory_idx,
    parse_table_idx,
)
from .text import (
    parse_text,
)

TExportDesc = Union[FunctionIdx, GlobalIdx, MemoryIdx, TableIdx]


def parse_export_descriptor(stream: IO[bytes]) -> TExportDesc:
    """
    Parse the descriptor value for an Export
    """
    flag = parse_single_byte(stream)

    if flag == 0x00:
        return parse_function_idx(stream)
    elif flag == 0x01:
        return parse_table_idx(stream)
    elif flag == 0x02:
        return parse_memory_idx(stream)
    elif flag == 0x03:
        return parse_global_idx(stream)
    else:
        raise MalformedModule(
            f"Unregonized byte while parsing export descriptor: {hex(flag)}"
        )


def parse_export(stream: IO[bytes]) -> Export:
    """
    Parser for the Export type
    """
    name = parse_text(stream)
    descriptor = parse_export_descriptor(stream)
    return Export(name, descriptor)
