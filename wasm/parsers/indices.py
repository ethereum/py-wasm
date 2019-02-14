from typing import IO

from wasm.datatypes import (
    FunctionIdx,
    GlobalIdx,
    LabelIdx,
    LocalIdx,
    MemoryIdx,
    TableIdx,
    TypeIdx,
)

from .integers import (
    parse_u32,
)


def parse_function_idx(stream: IO[bytes]) -> FunctionIdx:
    """
    Parser for the FunctionIdx type
    """
    raw_idx = parse_u32(stream)
    return FunctionIdx(raw_idx)


def parse_global_idx(stream: IO[bytes]) -> GlobalIdx:
    """
    Parser for the GlobalIdx type
    """
    raw_idx = parse_u32(stream)
    return GlobalIdx(raw_idx)


def parse_label_idx(stream: IO[bytes]) -> LabelIdx:
    """
    Parser for the LabelIdx type
    """
    raw_idx = parse_u32(stream)
    return LabelIdx(raw_idx)


def parse_local_idx(stream: IO[bytes]) -> LocalIdx:
    """
    Parser for the LocalIdx type
    """
    raw_idx = parse_u32(stream)
    return LocalIdx(raw_idx)


def parse_memory_idx(stream: IO[bytes]) -> MemoryIdx:
    """
    Parser for the MemoryIdx type
    """
    raw_idx = parse_u32(stream)
    return MemoryIdx(raw_idx)


def parse_table_idx(stream: IO[bytes]) -> TableIdx:
    """
    Parser for the TableIdx type
    """
    raw_idx = parse_u32(stream)
    return TableIdx(raw_idx)


def parse_type_idx(stream: IO[bytes]) -> TypeIdx:
    """
    Parser for the TypeIdx type
    """
    raw_idx = parse_u32(stream)
    return TypeIdx(raw_idx)
