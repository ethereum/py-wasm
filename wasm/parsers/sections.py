import functools
import io
import logging
from typing import (
    IO,
    Callable,
    Dict,
    Iterable,
    Iterator,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

import numpy

from wasm._utils.decorators import (
    to_tuple,
)
from wasm._utils.toolz import (
    groupby,
)
from wasm.datatypes import (
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
)
from wasm.exceptions import (
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

EMPTY_SECTIONS_BY_ID: Tuple[Tuple[int, SECTION_TYPES], ...] = (
    (0x01, TypeSection(tuple())),
    (0x02, ImportSection(tuple())),
    (0x03, FunctionSection(tuple())),
    (0x04, TableSection(tuple())),
    (0x05, MemorySection(tuple())),
    (0x06, GlobalSection(tuple())),
    (0x07, ExportSection(tuple())),
    (0x08, StartSection(None)),
    (0x09, ElementSegmentSection(tuple())),
    (0x0a, CodeSection(tuple())),
    (0x0b, DataSegmentSection(tuple())),
)

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
    """
    Helper function which validate that `values` is a length-1 tuple and then
    returns the tuple's sole value
    """
    if len(values) == 1:
        return values[0]
    elif not values:
        raise Exception("Invariant: empty")
    else:
        raise Exception(f"Invariant: multiple values {len(values)}")


TSection = TypeVar('TSection')


def normalize_sections(sections: Tuple[SECTION_TYPES, ...]) -> T_SECTIONS:
    """
    Helper to normalize the generated iterable of parsed module sections into a
    well structured data format.
    """
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


def parse_sections(stream: IO[bytes]) -> T_SECTIONS:
    """
    Parse the sections of a Web Assembly module.
    """
    sections = _parse_sections(stream)
    return normalize_sections(sections)


def _next_empty_section(section_id: numpy.uint8,
                        empty_sections_iter: Iterator[Tuple[int, SECTION_TYPES]]
                        ) -> Iterable[Tuple[int, SECTION_TYPES]]:
    """
    Helper function which returns *empty* versions of each section up to the
    provided `section_id`.
    """
    for empty_section_id, empty_section in empty_sections_iter:
        if empty_section_id != section_id:
            yield (empty_section_id, empty_section)
        else:
            break


@to_tuple
def _parse_sections(stream: IO[bytes]) -> Iterable[SECTION_TYPES]:
    """
    Helper function implementing the core logic for parsing sections.

    Among other things, this ensure that sections are correctly ordered and not
    duplicated (other than custom sections).
    """
    start_pos = stream.tell()
    end_pos = stream.seek(0, 2)
    stream.seek(start_pos)

    # During section parsing sections may be omitted.  The WASM spec says that
    # omitted sections are equivalent to them being present but empty.  As we
    # parse the bytecode, we need to fill in any missing sections with their
    # empty equivalent.  This iterator allows us to lazily step through the
    # sections in order.
    empty_section_iter = iter(EMPTY_SECTIONS_BY_ID)

    # A data structure to allow detection of duplicate sections.
    seen_section_ids: Set[int] = set()
    # We track missing sections separately.
    missing_section_ids: Set[int] = set()

    while stream.tell() < end_pos:
        section_id = parse_single_byte(stream)

        if section_id == numpy.uint8(0x00):
            yield parse_custom_section(stream)
            continue
        elif section_id not in PARSERS_BY_SECTION_ID:
            raise ParseError(f"Invalid section id: {hex(section_id)}")
        elif section_id in seen_section_ids:
            raise ParseError(
                f"Encountered multiple sections with the section id: "
                f"{hex(section_id)}"
            )
        elif section_id in missing_section_ids:
            all_seen = tuple(sorted(seen_section_ids.union(missing_section_ids)))
            raise ParseError(
                f"Encountered section id out of order. section_id={section_id} "
                f"already encountered sections {all_seen}"
            )

        seen_section_ids.add(section_id)

        for empty_id, empty_section in _next_empty_section(section_id, empty_section_iter):
            missing_section_ids.add(section_id)
            yield empty_section

        section_parser_fn = PARSERS_BY_SECTION_ID[section_id]
        section = section_parser_fn(stream)
        yield section

    # get empty sections for any that were omitted.
    for _, empty_section in empty_section_iter:
        yield empty_section


def validate_section_length(parser_fn: Callable[[IO[bytes]], TReturn]
                            ) -> Callable[[IO[bytes]], TReturn]:
    """
    Decorator for a section parser which wraps the parser such that it first
    reads the declared section length, then parses the section, and then
    validates that the parsed section's length matches the declared length.

    Raise a ParseError if the lengths do not match.
    """
    @functools.wraps(parser_fn)
    def parse_and_validate_length_fn(stream: IO[bytes]) -> TReturn:
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
        section = parser_fn(section_stream)

        current_pos = section_stream.tell()
        end_pos = section_stream.seek(0, 2)

        if current_pos != end_pos:
            raise ParseError(
                f"Section parser did not fully consume section stream, leaving "
                f"{end_pos - current_pos} unconsumed bytes"
            )
        return section
    return parse_and_validate_length_fn


#
# Custom
#
@validate_section_length
def parse_custom_section(stream: IO[bytes]) -> CustomSection:
    """
    Parser for the CustomSection type.
    """
    name = parse_text(stream)
    # Note that this **requires** that the main section parser feed this parser
    # a stream that **only** contains the section data since it blindly reads
    # till the end of the stream.
    binary = stream.read()

    return CustomSection(name, binary)


#
# Type (1)
#
@validate_section_length
def parse_type_section(stream: IO[bytes]) -> TypeSection:
    """
    Parser for the TypeSection type.
    """
    return TypeSection(parse_vector(parse_function_type, stream))


#
# Import (2)
#
@validate_section_length
def parse_import_section(stream: IO[bytes]) -> ImportSection:
    """
    Parser for the ImportSection type.
    """
    return ImportSection(parse_vector(parse_import, stream))


#
# Function (3)
#
@validate_section_length
def parse_function_section(stream: IO[bytes]) -> FunctionSection:
    """
    Parser for the FunctionSection type.
    """
    return FunctionSection(parse_vector(parse_type_idx, stream))


#
# Table (4)
#
@validate_section_length
def parse_table_section(stream: IO[bytes]) -> TableSection:
    """
    Parser for the TableSection type.
    """
    return TableSection(parse_vector(parse_table, stream))


#
# Memory (5)
#
@validate_section_length
def parse_memory_section(stream: IO[bytes]) -> MemorySection:
    """
    Parser for the MemorySection type.
    """
    return MemorySection(parse_vector(parse_memory, stream))


#
# Global (6)
#
@validate_section_length
def parse_global_section(stream: IO[bytes]) -> GlobalSection:
    """
    Parser for the GlobalSection type.
    """
    return GlobalSection(parse_vector(parse_global, stream))


#
# Export (7)
#
@validate_section_length
def parse_export_section(stream: IO[bytes]) -> ExportSection:
    """
    Parser for the ExportSection type.
    """
    return ExportSection(parse_vector(parse_export, stream))


#
# Start (8)
#
@validate_section_length
def parse_start_section(stream: IO[bytes]) -> StartSection:
    """
    Parser for the StartSection type.
    """
    return StartSection(parse_start_function(stream))


#
# Element Segment (9)
#
@validate_section_length
def parse_element_segment_section(stream: IO[bytes]) -> ElementSegmentSection:
    """
    Parser for the ElementSegmentSection type.
    """
    return ElementSegmentSection(parse_vector(parse_element_segment, stream))


#
# Code (10)
#
@validate_section_length
def parse_code_section(stream: IO[bytes]) -> CodeSection:
    """
    Parser for the CodeSection type.
    """
    return CodeSection(parse_vector(parse_code, stream))


#
# Data (11)
#
@validate_section_length
def parse_data_segment_section(stream: IO[bytes]) -> DataSegmentSection:
    """
    Parser for the DataSegmentSection type.
    """
    return DataSegmentSection(parse_vector(parse_data_segment, stream))


PARSERS_BY_SECTION_ID: Dict[numpy.uint8, Callable[[IO[bytes]], SECTION_TYPES]] = {
    numpy.uint8(0x01): parse_type_section,
    numpy.uint8(0x02): parse_import_section,
    numpy.uint8(0x03): parse_function_section,
    numpy.uint8(0x04): parse_table_section,
    numpy.uint8(0x05): parse_memory_section,
    numpy.uint8(0x06): parse_global_section,
    numpy.uint8(0x07): parse_export_section,
    numpy.uint8(0x08): parse_start_section,
    numpy.uint8(0x09): parse_element_segment_section,
    numpy.uint8(0x0a): parse_code_section,
    numpy.uint8(0x0b): parse_data_segment_section,
}
