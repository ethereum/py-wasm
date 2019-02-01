import io

from wasm import (
    constants,
)
from wasm.datatypes import (
    Code,
    LocalsMeta,
)
from wasm.exceptions import (
    MalformedModule,
)

from .expressions import (
    parse_expression,
)
from .integers import (
    parse_u32,
)
from .valtype import (
    parse_valtype,
)
from .vector import (
    parse_vector,
)


def parse_locals(stream: io.BytesIO) -> LocalsMeta:
    num = parse_u32(stream)
    valtype = parse_valtype(stream)
    return LocalsMeta(num, valtype)


def parse_code(stream: io.BytesIO) -> Code:
    size = parse_u32(stream)
    start_pos = stream.tell()
    expected_end_pos = start_pos + size

    locals = parse_vector(parse_locals, stream)

    num_locals = sum(local.num for local in locals)
    if num_locals > constants.UINT32_MAX:
        raise MalformedModule(
            f"Number of locals exceeds u32: {num_locals} > "
            f"{constants.UINT32_MAX}"
        )

    expr = parse_expression(stream)

    end_pos = stream.tell()
    if end_pos != expected_end_pos:
        actual_size = end_pos - start_pos
        raise MalformedModule(
            f"Declared code size does not match parsed size: Declared={size} "
            f"Actual={actual_size}"
        )
    local_types = tuple(
        local.valtype
        for local in locals
        for _ in range(local.num)
    )
    return Code(local_types, expr)
