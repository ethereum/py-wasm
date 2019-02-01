import io
from typing import (
    Union,
)

from wasm.datatypes import (
    Export,
    FuncIdx,
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
    parse_func_idx,
    parse_global_idx,
    parse_memory_idx,
    parse_table_idx,
)
from .text import (
    parse_text,
)

TExportDesc = Union[FuncIdx, GlobalIdx, MemoryIdx, TableIdx]


def parse_export_descriptor(stream: io.BytesIO) -> TExportDesc:
    flag = parse_single_byte(stream)

    if flag == 0x00:
        return parse_func_idx(stream)
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


def parse_export(stream: io.BytesIO) -> Export:
    name = parse_text(stream)
    descriptor = parse_export_descriptor(stream)
    return Export(name, descriptor)
