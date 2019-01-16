from wasm import (
    constants,
)


def is_float_type(type_: str) -> bool:
    return type_ in constants.FLOAT_TYPES


def is_integer_type(type_: str) -> bool:
    return type_ in constants.INTEGER_TYPES


def get_integer_type(num_bits: int) -> str:
    if num_bits == 32:
        return constants.INT32
    elif num_bits == 64:
        return constants.INT64
    else:
        raise ValueError("Invalid bit size.  Must be 32 or 64")


def get_float_type(num_bits: int) -> str:
    if num_bits == 32:
        return constants.FLOAT32
    elif num_bits == 64:
        return constants.FLOAT64
    else:
        raise ValueError("Invalid bit size.  Must be 32 or 64")


BIT_SIZES = {
    constants.INT32: 32,
    constants.INT64: 64,
    constants.FLOAT32: 32,
    constants.FLOAT64: 64,
}


def get_bit_size(type_: str) -> int:
    try:
        return BIT_SIZES[type_]
    except KeyError:
        raise ValueError(f"Invalid type: Must be one of i32/i64/f32/f64 - Got {type_}")
