import struct


def int_to_float(num_bits: int, value: int) -> float:
    """
    Convert an integer to the equivalent floating point value.
    """
    if num_bits == 32:
        unpack_fmt = '>f'
    elif num_bits == 64:
        unpack_fmt = '>d'
    else:
        raise Exception(f"Unhandled bit size: {num_bits}")

    return struct.unpack(unpack_fmt, value.to_bytes(num_bits // 8, 'big'))[0]


def get_bit_size(_type: str) -> int:
    if _type in {'i32', 'f32'}:
        return 32
    elif _type in {'i64', 'f64'}:
        return 64
    else:
        raise ValueError(f"Unsupported type: {_type}")
