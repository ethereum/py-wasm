from typing import IO

from wasm.exceptions import (
    MalformedModule,
    ParseError,
)

from .size import (
    parse_size,
)


def parse_text(stream: IO[bytes]) -> str:
    encoded_name_length = parse_size(stream)
    encoded_name = stream.read(encoded_name_length)

    if len(encoded_name) != encoded_name_length:
        raise ParseError(
            "Unexpected end of stream while parsing name. Expected length "
            f"{encoded_name_length}.  Got '{encoded_name} with length "
            f"{len(encoded_name)}")

    try:
        name = encoded_name.decode('utf8')
    except UnicodeDecodeError as err:
        raise MalformedModule from err

    return name
