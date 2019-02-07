import struct
from typing import (
    Union,
)

from wasm.typing import (
    Float32,
    Float64,
)


def int_to_float(num_bits: int, value: int) -> Union[Float32, Float64]:
    """
    Convert an integer to the equivalent floating point value.
    """
    value_as_bytes = value.to_bytes(num_bits // 8, 'big')

    if num_bits == 32:
        return Float32(struct.unpack('>f', value_as_bytes)[0])
    elif num_bits == 64:
        return Float32(struct.unpack('>d', value_as_bytes)[0])
    else:
        raise Exception(f"Unhandled bit size: {num_bits}")


def get_bit_size(_type: str) -> int:
    if _type in {'i32', 'f32'}:
        return 32
    elif _type in {'i64', 'f64'}:
        return 64
    else:
        raise ValueError(f"Unsupported type: {_type}")
