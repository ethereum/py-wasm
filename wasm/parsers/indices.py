import io

from wasm.datatypes import (
    FuncIdx,
    GlobalIdx,
    LabelIdx,
    LocalIdx,
    TypeIdx,
)

from .integers import (
    parse_u32,
)


def parse_funcidx(stream: io.BytesIO) -> FuncIdx:
    raw_idx = parse_u32(stream)
    return FuncIdx(raw_idx)


def parse_globalidx(stream: io.BytesIO) -> GlobalIdx:
    raw_idx = parse_u32(stream)
    return GlobalIdx(raw_idx)


def parse_labelidx(stream: io.BytesIO) -> LabelIdx:
    raw_idx = parse_u32(stream)
    return LabelIdx(raw_idx)


def parse_localidx(stream: io.BytesIO) -> LocalIdx:
    raw_idx = parse_u32(stream)
    return LocalIdx(raw_idx)


def parse_typeidx(stream: io.BytesIO) -> TypeIdx:
    raw_idx = parse_u32(stream)
    return TypeIdx(raw_idx)
