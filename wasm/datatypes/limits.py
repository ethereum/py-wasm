from typing import (
    NamedTuple,
    Optional,
)

import numpy


class Limits(NamedTuple):
    min: numpy.uint32
    max: Optional[numpy.uint32]
