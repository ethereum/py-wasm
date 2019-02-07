from typing import IO

from wasm.datatypes import (
    Global,
    GlobalType,
)

from .expressions import (
    parse_expression,
)
from .mutability import (
    parse_mut,
)
from .valtype import (
    parse_valtype,
)


def parse_global_type(stream: IO[bytes]) -> GlobalType:
    valtype = parse_valtype(stream)
    mut = parse_mut(stream)
    return GlobalType(mut, valtype)


def parse_global(stream: IO[bytes]) -> Global:
    global_type = parse_global_type(stream)
    init = parse_expression(stream)
    return Global(global_type, init)
