from typing import IO

import numpy


def parse_f32(stream: IO[bytes]) -> numpy.float32:
    """
    Parser for 32-bit floats
    """
    raw_buffer = stream.read(4)
    buffer = bytes(raw_buffer)
    if len(buffer) < 4:
        raise Exception("TODO: better exception for insufficient bytes")

    return numpy.frombuffer(buffer, numpy.float32)[0]


def parse_f64(stream: IO[bytes]) -> numpy.float64:
    """
    Parser for 64-bit floats
    """
    raw_buffer = stream.read(8)
    buffer = bytes(raw_buffer)
    if len(buffer) < 8:
        raise Exception("TODO: better exception for insufficient bytes")

    return numpy.frombuffer(buffer, numpy.float64)[0]
