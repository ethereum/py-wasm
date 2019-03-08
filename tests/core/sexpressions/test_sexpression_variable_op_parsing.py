import pytest

from wasm.text import parse
from wasm.text.ir import UnresolvedVariableOp
from wasm.datatypes import (
    LocalIdx,
    GlobalIdx,
)
from wasm.instructions.variable import (
    LocalOp,
    GlobalOp,
)
from wasm.opcodes import BinaryOpcode


@pytest.mark.parametrize(
    'sexpr,expected',
    (
        ("(local.get $i)", UnresolvedVariableOp(BinaryOpcode.GET_LOCAL, '$i')),
        ("(local.get 1)", LocalOp.from_opcode(BinaryOpcode.GET_LOCAL, LocalIdx(1))),
        ("(local.set $i)", UnresolvedVariableOp(BinaryOpcode.SET_LOCAL, '$i')),
        ("(local.set 1)", LocalOp.from_opcode(BinaryOpcode.SET_LOCAL, LocalIdx(1))),
        ("(local.tee $i)", UnresolvedVariableOp(BinaryOpcode.TEE_LOCAL, '$i')),
        ("(local.tee 1)", LocalOp.from_opcode(BinaryOpcode.TEE_LOCAL, LocalIdx(1))),
        ("(global.get $i)", UnresolvedVariableOp(BinaryOpcode.GET_GLOBAL, '$i')),
        ("(global.get 1)", GlobalOp.from_opcode(BinaryOpcode.GET_GLOBAL, GlobalIdx(1))),
        ("(global.set $i)", UnresolvedVariableOp(BinaryOpcode.SET_GLOBAL, '$i')),
        ("(global.set 1)", GlobalOp.from_opcode(BinaryOpcode.SET_GLOBAL, GlobalIdx(1))),
    ),
)
def test_sexpression_local_variable_parsing(sexpr, expected):
    actual = parse(sexpr)
    assert actual == expected
