import io
import logging
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from wasm._utils.toolz import (
    groupby,
)
from wasm.datatypes import (
    Code,
    CodeSection,
    CustomSection,
    DataSegment,
    DataSegmentSection,
    ElementSegment,
    ElementSegmentSection,
    Export,
    ExportSection,
    FunctionSection,
    FunctionType,
    Global,
    GlobalSection,
    Import,
    ImportSection,
    Memory,
    MemorySection,
    StartSection,
    Table,
    TableSection,
    TypeIdx,
    TypeSection,
)
from wasm.exceptions import (
    MalformedModule,
    ParseError,
)

from .byte import (
    parse_single_byte,
)
from .code import (
    parse_code,
)
from .data_segment import (
    parse_data_segment,
)
from .element_segment import (
    parse_element_segment,
)
from .exports import (
    parse_export,
)
from .functions import (
    parse_function_type,
    parse_start_function,
)
from .globals import (
    parse_global,
)
from .imports import (
    parse_import,
)
from .indices import (
    parse_type_idx,
)
from .integers import (
    parse_u32,
)
from .memory import (
    parse_memory,
)
from .tables import (
    parse_table,
)
from .text import (
    parse_text,
)
from .vector import (
    parse_vector,
)

logger = logging.getLogger('wasm.parsers.sections')


TReturn = TypeVar('TReturn')


KNOWN_SECTION_IDS = {
    0x01,
    0x02,
    0x03,
    0x04,
    0x05,
    0x06,
    0x07,
    0x08,
    0x09,
    0x0a,
    0x0b,
}

EMPTY_SECTIONS_BY_ID = {
    0x01: TypeSection(tuple()),
    0x02: ImportSection(tuple()),
    0x03: FunctionSection(tuple()),
    0x04: TableSection(tuple()),
    0x05: MemorySection(tuple()),
    0x06: GlobalSection(tuple()),
    0x07: ExportSection(tuple()),
    0x08: StartSection(None),
    0x09: ElementSegmentSection(tuple()),
    0x0a: CodeSection(tuple()),
    0x0b: DataSegmentSection(tuple()),
}

SECTION_TYPES = Union[
    CodeSection,
    CustomSection,
    DataSegmentSection,
    ElementSegmentSection,
    ExportSection,
    FunctionSection,
    GlobalSection,
    ImportSection,
    MemorySection,
    StartSection,
    TableSection,
    TypeSection,
]

T_SECTIONS = Tuple[
    Tuple[CustomSection, ...],
    TypeSection,
    ImportSection,
    FunctionSection,
    TableSection,
    MemorySection,
    GlobalSection,
    ExportSection,
    StartSection,
    ElementSegmentSection,
    CodeSection,
    DataSegmentSection,
]


def _get_single_or_raise(values: Tuple[TReturn, ...]) -> TReturn:
    if len(values) == 1:
        return values[0]
    elif not values:
        raise Exception("Invariant: empty")
    else:
        raise Exception(f"Invariant: multiple values {len(values)}")


TSection = TypeVar('TSection')


def normalize_sections(sections: Tuple[SECTION_TYPES, ...]) -> T_SECTIONS:
    sections_by_type: Dict[Type, Tuple[SECTION_TYPES, ...]] = groupby(type, sections)

    # 0
    custom_sections: Tuple[CustomSection, ...] = cast(
        Tuple[CustomSection, ...],
        sections_by_type.get(CustomSection, tuple()),
    )
    # 1
    type_section: TypeSection = cast(
        TypeSection,
        _get_single_or_raise(sections_by_type[TypeSection]),
    )
    # 2
    import_section: ImportSection = cast(
        ImportSection,
        _get_single_or_raise(sections_by_type[ImportSection]),
    )
    # 3
    function_section: FunctionSection = cast(
        FunctionSection,
        _get_single_or_raise(sections_by_type[FunctionSection]),
    )
    # 4
    table_section: TableSection = cast(
        TableSection,
        _get_single_or_raise(sections_by_type[TableSection]),
    )
    # 5
    memory_section: MemorySection = cast(
        MemorySection,
        _get_single_or_raise(sections_by_type[MemorySection]),
    )
    # 6
    global_section: GlobalSection = cast(
        GlobalSection,
        _get_single_or_raise(sections_by_type[GlobalSection]),
    )
    # 7
    export_section: ExportSection = cast(
        ExportSection,
        _get_single_or_raise(sections_by_type[ExportSection]),
    )
    # 8
    start_section: StartSection = cast(
        StartSection,
        _get_single_or_raise(sections_by_type[StartSection]),
    )
    # 9
    element_segment_section: ElementSegmentSection = cast(
        ElementSegmentSection,
        _get_single_or_raise(sections_by_type[ElementSegmentSection]),
    )
    # 10
    code_section: CodeSection = cast(
        CodeSection,
        _get_single_or_raise(sections_by_type[CodeSection]),
    )
    # 11
    data_segment_section: DataSegmentSection = cast(
        DataSegmentSection,
        _get_single_or_raise(sections_by_type[DataSegmentSection]),
    )

    return (
        custom_sections,
        type_section,
        import_section,
        function_section,
        table_section,
        memory_section,
        global_section,
        export_section,
        start_section,
        element_segment_section,
        code_section,
        data_segment_section,
    )


def parse_sections(stream: io.BytesIO) -> T_SECTIONS:
    sections = tuple(_parse_sections(stream))
    return normalize_sections(sections)


def _parse_sections(stream: io.BytesIO) -> Iterable[Any]:
    start_pos = stream.tell()
    end_pos = stream.seek(0, 2)
    stream.seek(start_pos)

    # We create an iterator so that during parsing we can
    parser_iter = iter(ordered_parsers_by_section_id)
    seen_section_ids = set()

    while stream.tell() < end_pos:
        section_id = parse_single_byte(stream)

        if section_id == 0x00:
            yield parse_custom_section(stream)
            continue
        elif section_id not in KNOWN_SECTION_IDS:
            raise MalformedModule(f"Invalid section id: {hex(section_id)}")

        for parser_section_id, section_parser in parser_iter:
            if section_id == parser_section_id:
                yield section_parser(stream)
                # Track which section ids we've encountered.
                seen_section_ids.add(section_id)
                break
            else:
                yield EMPTY_SECTIONS_BY_ID[parser_section_id]
        else:
            # If the loop above exits naturally, it means that we've
            # encountered a section out of order or multiple times.
            if section_id in seen_section_ids:
                raise MalformedModule(
                    f"Encountered multiple sections with the section id: "
                    f"{hex(section_id)}"
                )
            elif section_id < max(seen_section_ids):
                raise MalformedModule(
                    f"Encountered section id out of order.  id={section_id} "
                    f"already_seen={tuple(sorted(seen_section_ids))}"
                )
            else:
                raise Exception("Invariant: unreachable code path")

    # Generate empties for any sections that were left off.
    for parser_section_id, _ in parser_iter:
        yield EMPTY_SECTIONS_BY_ID[parser_section_id]


def _parse_single_section(body_parser: Callable[[io.BytesIO], TReturn],
                          stream: io.BytesIO) -> TReturn:
    """
    Wrapper around section parsing to ensure that the declared size and the
    parsed size match.
    """
    # Note: Section parsers all operate under the assumption that their `stream`
    # contains **only** the bytes for the given section.  It follows that
    # successful parsing for any section **must** consume the full stream.
    declared_size = parse_u32(stream)
    raw_section = stream.read(declared_size)

    if len(raw_section) != declared_size:
        raise ParseError(
            "Section declared size larger than stream. "
            "declared={declared_size}  actual={len(raw_section)}"
        )

    section_stream = io.BytesIO(raw_section)
    section = body_parser(section_stream)

    current_pos = section_stream.tell()
    end_pos = section_stream.seek(0, 2)

    if current_pos != end_pos:
        raise ParseError(
            f"Section parser did not fully consume section stream, leaving "
            f"{end_pos - current_pos} unconsumed bytes"
        )
    return section


#
# Custom
#
def parse_custom_section(stream: io.BytesIO) -> CustomSection:
    return _parse_single_section(parse_custom_section_body, stream)


def parse_custom_section_body(stream: io.BytesIO) -> CustomSection:
    name = parse_text(stream)
    binary = stream.read()

    return CustomSection(name, binary)


#
# Type (1)
#
def parse_type_section_body(stream: io.BytesIO) -> Tuple[FunctionType, ...]:
    return parse_vector(parse_function_type, stream)


def parse_type_section(stream: io.BytesIO) -> TypeSection:
    functions = _parse_single_section(parse_type_section_body, stream)
    return TypeSection(functions)


#
# Import (2)
#
def parse_import_section_body(stream: io.BytesIO) -> Tuple[Import, ...]:
    return parse_vector(parse_import, stream)


def parse_import_section(stream: io.BytesIO) -> ImportSection:
    imports = _parse_single_section(parse_import_section_body, stream)
    return ImportSection(imports)


#
# Function (3)
#
def parse_function_section_body(stream: io.BytesIO) -> Tuple[TypeIdx, ...]:
    return parse_vector(parse_type_idx, stream)


def parse_function_section(stream: io.BytesIO) -> FunctionSection:
    types = _parse_single_section(parse_function_section_body, stream)
    return FunctionSection(types)


#
# Table (4)
#
def parse_table_section_body(stream: io.BytesIO) -> Tuple[Table, ...]:
    return parse_vector(parse_table, stream)


def parse_table_section(stream: io.BytesIO) -> TableSection:
    tables = _parse_single_section(parse_table_section_body, stream)
    return TableSection(tables)


#
# Memory (5)
#
def parse_memory_section_body(stream: io.BytesIO) -> Tuple[Memory, ...]:
    return parse_vector(parse_memory, stream)


def parse_memory_section(stream: io.BytesIO) -> MemorySection:
    mems = _parse_single_section(parse_memory_section_body, stream)
    return MemorySection(mems)


#
# Global (6)
#
def parse_global_section_body(stream: io.BytesIO) -> Tuple[Global, ...]:
    return parse_vector(parse_global, stream)


def parse_global_section(stream: io.BytesIO) -> GlobalSection:
    globals = _parse_single_section(parse_global_section_body, stream)
    return GlobalSection(globals)


#
# Export (7)
#
def parse_export_section_body(stream: io.BytesIO) -> Tuple[Export, ...]:
    return parse_vector(parse_export, stream)


def parse_export_section(stream: io.BytesIO) -> ExportSection:
    exports = _parse_single_section(parse_export_section_body, stream)
    return ExportSection(exports)


#
# Start (8)
#
def parse_start_section(stream: io.BytesIO) -> StartSection:
    start_function = _parse_single_section(parse_start_function, stream)
    return StartSection(start_function)


#
# Element Segment (9)
#
def parse_element_segment_section_body(stream: io.BytesIO) -> Tuple[ElementSegment, ...]:
    return parse_vector(parse_element_segment, stream)


def parse_element_segment_section(stream: io.BytesIO) -> ElementSegmentSection:
    element_segments = _parse_single_section(parse_element_segment_section_body, stream)
    return ElementSegmentSection(element_segments)


#
# Code (10)
#
def parse_code_section_body(stream: io.BytesIO) -> Tuple[Code, ...]:
    return parse_vector(parse_code, stream)


def parse_code_section(stream: io.BytesIO) -> CodeSection:
    codes = _parse_single_section(parse_code_section_body, stream)
    return CodeSection(codes)


#
# Data (11)
#
def parse_data_segment_section_body(stream: io.BytesIO) -> Tuple[DataSegment, ...]:
    return parse_vector(parse_data_segment, stream)


def parse_data_segment_section(stream: io.BytesIO) -> DataSegmentSection:
    data_segments = _parse_single_section(parse_data_segment_section_body, stream)
    return DataSegmentSection(data_segments)


ordered_parsers_by_section_id = (
    (0x01, parse_type_section),
    (0x02, parse_import_section),
    (0x03, parse_function_section),
    (0x04, parse_table_section),
    (0x05, parse_memory_section),
    (0x06, parse_global_section),
    (0x07, parse_export_section),
    (0x08, parse_start_section),
    (0x09, parse_element_segment_section),
    (0x0a, parse_code_section),
    (0x0b, parse_data_segment_section),
)
