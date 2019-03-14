import io

import pytest

from wasm.exceptions import (
    MalformedModule,
)
from wasm.opcodes import (
    BinaryOpcode,
)
from wasm.binary.numeric import (
    parse_numeric_constant_instruction,
)


@pytest.mark.parametrize(
    "opcode,raw_value",
    (
        # exceeds allowed bit width
        (BinaryOpcode.I32_CONST, b'\x80\x80\x80\x80\x80\x00'),
        (BinaryOpcode.I32_CONST, b'\xff\xff\xff\xff\x0f'),
        (BinaryOpcode.I64_CONST, b'\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x00'),
        (BinaryOpcode.I64_CONST, b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\x0f'),
    ),
)
def test_parse_numeric_constant_instruction(opcode, raw_value):
    with pytest.raises(MalformedModule):
        parse_numeric_constant_instruction(opcode, io.BytesIO(raw_value))
