import sys

from .datatypes import (  # noqa: F401
    Store,
)
from .execution import (  # noqa: F401
    Runtime,
)

if sys.byteorder != 'little':
    raise ImportError(
        f"WebAssembly operates on little endian encoded values. This library's "
        f"use of numpy uses the system's endianness.  The current system's "
        f"endianness is {sys.byteorder} which isn't compatible."
    )
