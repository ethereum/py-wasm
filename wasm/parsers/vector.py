import io
from typing import (
    Callable,
    Iterable,
    Tuple,
    TypeVar,
)

from wasm.exceptions import (
    ParseError,
)
from wasm.typing import (
    UInt32,
)

from .integers import (
    parse_u32,
)

TItem = TypeVar('TItem')


def parse_vector(sub_parser: Callable[[io.BytesIO], TItem],
                 stream: io.BytesIO,
                 ) -> Tuple[TItem, ...]:
    vector_size = parse_u32(stream)
    try:
        return tuple(_parse_vector(sub_parser, vector_size, stream))
    except Exception as err:
        raise ParseError(f"Error parsing vector: {err}") from err


def _parse_vector(sub_parser: Callable[[io.BytesIO], TItem],
                  vector_size: UInt32,
                  stream: io.BytesIO,
                  ) -> Iterable[TItem]:
    for _ in range(vector_size):
        yield sub_parser(stream)
