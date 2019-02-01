import io

from wasm.datatypes import (
    ElementSegment,
)

from .expressions import (
    parse_expression,
)
from .indices import (
    parse_func_idx,
    parse_table_idx,
)
from .vector import (
    parse_vector,
)


def parse_element_segment(stream: io.BytesIO) -> ElementSegment:
    table_idx = parse_table_idx(stream)
    offset = parse_expression(stream)
    init = parse_vector(parse_func_idx, stream)
    return ElementSegment(table_idx, offset, init)
