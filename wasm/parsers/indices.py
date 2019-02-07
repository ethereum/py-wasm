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
    raw_idx = parse_u32(stream)
    return FunctionIdx(raw_idx)


def parse_global_idx(stream: IO[bytes]) -> GlobalIdx:
    raw_idx = parse_u32(stream)
    return GlobalIdx(raw_idx)


def parse_label_idx(stream: IO[bytes]) -> LabelIdx:
    raw_idx = parse_u32(stream)
    return LabelIdx(raw_idx)


def parse_local_idx(stream: IO[bytes]) -> LocalIdx:
    raw_idx = parse_u32(stream)
    return LocalIdx(raw_idx)


def parse_memory_idx(stream: IO[bytes]) -> MemoryIdx:
    raw_idx = parse_u32(stream)
    return MemoryIdx(raw_idx)


def parse_table_idx(stream: IO[bytes]) -> TableIdx:
    raw_idx = parse_u32(stream)
    return TableIdx(raw_idx)


def parse_type_idx(stream: IO[bytes]) -> TypeIdx:
    raw_idx = parse_u32(stream)
    return TypeIdx(raw_idx)
