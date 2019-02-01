import io

from wasm.datatypes import (
    FuncIdx,
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


def parse_func_idx(stream: io.BytesIO) -> FuncIdx:
    raw_idx = parse_u32(stream)
    return FuncIdx(raw_idx)


def parse_global_idx(stream: io.BytesIO) -> GlobalIdx:
    raw_idx = parse_u32(stream)
    return GlobalIdx(raw_idx)


def parse_label_idx(stream: io.BytesIO) -> LabelIdx:
    raw_idx = parse_u32(stream)
    return LabelIdx(raw_idx)


def parse_local_idx(stream: io.BytesIO) -> LocalIdx:
    raw_idx = parse_u32(stream)
    return LocalIdx(raw_idx)


def parse_memory_idx(stream: io.BytesIO) -> MemoryIdx:
    raw_idx = parse_u32(stream)
    return MemoryIdx(raw_idx)


def parse_table_idx(stream: io.BytesIO) -> TableIdx:
    raw_idx = parse_u32(stream)
    return TableIdx(raw_idx)


def parse_type_idx(stream: io.BytesIO) -> TypeIdx:
    raw_idx = parse_u32(stream)
    return TypeIdx(raw_idx)
