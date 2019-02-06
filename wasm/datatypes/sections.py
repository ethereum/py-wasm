from typing import (
    NamedTuple,
    Optional,
    Tuple,
)

from .code import (
    Code,
)
from .data_segment import (
    DataSegment,
)
from .element_segment import (
    ElementSegment,
)
from .exports import (
    Export,
)
from .function import (
    FunctionType,
    StartFunction,
)
from .globals import (
    Global,
)
from .imports import (
    Import,
)
from .indices import (
    TypeIdx,
)
from .memory import (
    Memory,
)
from .table import (
    Table,
)


class CustomSection(NamedTuple):
    name: str
    binary: bytes


class TypeSection(NamedTuple):
    function_types: Tuple[FunctionType, ...]


class ImportSection(NamedTuple):
    imports: Tuple[Import, ...]


class FunctionSection(NamedTuple):
    types: Tuple[TypeIdx, ...]


class TableSection(NamedTuple):
    tables: Tuple[Table, ...]


class MemorySection(NamedTuple):
    mems: Tuple[Memory, ...]


class GlobalSection(NamedTuple):
    globals: Tuple[Global, ...]


class ExportSection(NamedTuple):
    exports: Tuple[Export, ...]


class StartSection(NamedTuple):
    start: Optional[StartFunction]


class ElementSegmentSection(NamedTuple):
    element_segments: Tuple[ElementSegment, ...]


class CodeSection(NamedTuple):
    codes: Tuple[Code, ...]


class DataSegmentSection(NamedTuple):
    data_segments: Tuple[DataSegment, ...]
