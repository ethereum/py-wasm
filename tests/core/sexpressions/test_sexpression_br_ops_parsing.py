import pytest

from wasm.text import parse
from wasm.datatypes import (
    LabelIdx,
)
from wasm.instructions.control import (
    Br,
    BrIf,
    BrTable,
)
from wasm.text.ir import (
    UnresolvedBr,
    UnresolvedBrIf,
    UnresolvedBrTable,
    UnresolvedLabelIdx,
)


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ("(br 0)", Br(LabelIdx(0))),
        ("(br $i)", UnresolvedBr(UnresolvedLabelIdx('$i'))),
        ("(br_if 0)", BrIf(LabelIdx(0))),
        ("(br_if $i)", UnresolvedBrIf(UnresolvedLabelIdx('$i'))),
        ("(br_table 1 2 3)", BrTable((LabelIdx(1), LabelIdx(2)), LabelIdx(3))),
        (
            "(br_table 1 2 $default)",
            UnresolvedBrTable((LabelIdx(1), LabelIdx(2)), UnresolvedLabelIdx('$default')),
        ),
        (
            "(br_table 1 2 $three 4)",
            UnresolvedBrTable(
                (LabelIdx(1), LabelIdx(2), UnresolvedLabelIdx('$three')),
                LabelIdx(4),
            ),
        ),
    ),
)
def test_sexpression_br_instructions_parsing(sexpr, expected):
    actual, = parse(sexpr)
    assert actual == expected
