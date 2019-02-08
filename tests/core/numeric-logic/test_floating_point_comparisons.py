import itertools
import math

import pytest

from wasm.datatypes import (
    Store,
)
from wasm.execution import (
    Configuration,
    Frame,
)
from wasm.instructions import (
    RelOp,
    End,
)
from wasm.opcodes import (
    BinaryOpcode,
)


@pytest.fixture
def config():
    return Configuration(Store())


@pytest.mark.parametrize(
    "opcode,operands_and_expected",
    itertools.chain(
        itertools.product(
            (BinaryOpcode.F32_LT, BinaryOpcode.F64_LT),
            (
                ((0.0, 0.0), (0,)),
                ((1.0, 1.0), (0,)),
                # nans
                ((math.nan, 0), (0,)),
                ((0.0, math.nan), (0,)),
                ((math.nan, math.nan), (0,)),
                # a is inf
                ((math.inf, 0.0), (0,)),
                ((math.inf, math.inf), (0,)),
                # a is -inf
                ((-math.inf, 0.0), (1,)),
                ((-math.inf, -math.inf), (1,)),
                # b is inf
                ((0.0, math.inf), (1,)),
                # b is -inf
                ((0.0, -math.inf), (0,)),
            ),
        ),
        itertools.product(
            (BinaryOpcode.F32_GT, BinaryOpcode.F64_GT),
            (
                ((0.0, 0.0), (0,)),
                ((1.0, 1.0), (0,)),
                # nans
                ((math.nan, 0.0), (0,)),
                ((0.0, math.nan), (0,)),
                ((math.nan, math.nan), (0,)),
                # a is inf
                ((math.inf, 0.0), (1,)),
                ((math.inf, math.inf), (1,)),
                # a is -inf
                ((-math.inf, 0.0), (0,)),
                ((-math.inf, -math.inf), (0,)),
                # b is inf
                ((0.0, math.inf), (0,)),
                # b is -inf
                ((0.0, -math.inf), (1,)),
            ),
        ),
        itertools.product(
            (BinaryOpcode.F32_LE, BinaryOpcode.F64_LE),
            (
                ((0.0, 0.0), (1,)),
                ((1.0, 1.0), (1,)),
                # nans
                ((math.nan, 0), (0,)),
                ((0.0, math.nan), (0,)),
                ((math.nan, math.nan), (0,)),
                # a is inf
                ((math.inf, 0.0), (0,)),
                ((math.inf, math.inf), (0,)),
                # a is -inf
                ((-math.inf, 0.0), (1,)),
                ((-math.inf, -math.inf), (1,)),
                # b is inf
                ((0.0, math.inf), (1,)),
                # b is -inf
                ((0.0, -math.inf), (0,)),
            ),
        ),
        itertools.product(
            (BinaryOpcode.F32_GE, BinaryOpcode.F64_GE),
            (
                ((0.0, 0.0), (1,)),
                ((1.0, 1.0), (1,)),
                # nans
                ((math.nan, 0.0), (0,)),
                ((0.0, math.nan), (0,)),
                ((math.nan, math.nan), (0,)),
                # a is inf
                ((math.inf, 0.0), (1,)),
                ((math.inf, math.inf), (1,)),
                # a is -inf
                ((-math.inf, 0.0), (0,)),
                ((-math.inf, -math.inf), (0,)),
                # b is inf
                ((0.0, math.inf), (0,)),
                # b is -inf
                ((0.0, -math.inf), (1,)),
            ),
        ),
    ),
)
def test_float_comparison_operations(config, opcode, operands_and_expected):
    operands, expected = operands_and_expected
    frame = Frame(None, [], (RelOp.from_opcode(opcode), End()), len(expected))
    config.push_frame(frame)
    config.extend_operands(operands)

    results = config.execute()
    assert results == expected
