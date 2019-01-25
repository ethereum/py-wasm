import pytest

from wasm.opcodes import (
    BinaryOpcode,
)
from wasm.opcodes.text import (
    OPCODE_TO_TEXT,
)


@pytest.mark.parametrize(
    'opcode',
    tuple(iter(BinaryOpcode)),
)
def test_all_opcodes_have_text_representations(opcode):
    assert opcode.text


def test_no_extra_text_values_for_opcodes():
    all_opcode_texts = set(opcode.text for opcode in BinaryOpcode)
    all_raw_texts = set(OPCODE_TO_TEXT.values())

    assert all_opcode_texts == all_raw_texts
    assert len(all_opcode_texts) == len(BinaryOpcode)
