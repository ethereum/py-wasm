from typing import IO

from wasm.datatypes import (
    FunctionType,
    StartFunction,
)
from wasm.exceptions import (
    MalformedModule,
)

from .byte import (
    parse_single_byte,
)
from .indices import (
    parse_function_idx,
)
from .valtype import (
    parse_valtype,
)
from .vector import (
    parse_vector,
)


def parse_function_type(stream: IO[bytes]) -> FunctionType:
    """
    Parser for the FunctionType type.
    """
    flag = parse_single_byte(stream)

    if flag != 0x60:
        raise MalformedModule(
            f"Invalid function type leading byte: {hex(flag)}"
        )

    params = parse_vector(parse_valtype, stream)
    results = parse_vector(parse_valtype, stream)

    return FunctionType(params, results)


def parse_start_function(stream: IO[bytes]) -> StartFunction:
    """
    Parser for the StartFunction type
    """
    function_idx = parse_function_idx(stream)
    return StartFunction(function_idx)
