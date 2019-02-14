from pathlib import (
    Path,
)
from typing import (
    NamedTuple,
    Optional,
    Tuple,
    Union,
)

from wasm.datatypes import (
    ValType,
)
from wasm.typing import (
    TValue,
)


class ModuleCommand(NamedTuple):
    line: int
    file_path: Path
    name: Optional[str]


class Argument(NamedTuple):
    valtype: ValType
    value: TValue


class Expected(NamedTuple):
    valtype: ValType
    value: Union[None, TValue]


class Action(NamedTuple):
    type: str
    field: str
    module: Optional[str]
    args: Tuple[Argument, ...]


class AssertReturnCommand(NamedTuple):
    line: int
    action: Action
    expected: Tuple[Expected, ...]


class AssertInvalidCommand(NamedTuple):
    line: int
    file_path: Path
    text: str
    module_type: str


class AssertTrap(NamedTuple):
    '''
    {
        "type": "assert_trap",
        "line": 192,
        "action": {
            "type": "invoke",
            "field": "32_good5",
            "args": [
                {"type": "i32",
                "value": "65508"}
            ],
        },
        "text": "out of bounds memory access",
        "expected": [
            {"type": "i32"}
        ]
    }
    '''
    line: int
    action: Action
    text: str
    expected: Tuple[Expected, ...]


class AssertMalformed(NamedTuple):
    '''
    {
        "type": "assert_malformed",
        "line": 207,
        "filename": "address.wast.1.wat",
        "text": "i32 constant",
        "module_type": "text"
    }
    '''
    line: int
    file_path: Path
    text: str
    module_type: str


class AssertExhaustion(NamedTuple):
    '''
    {
        "type": "assert_exhaustion",
        "line": 153,
        "action": {
            "type": "invoke",
            "field": "runaway",
            "args": []
        },
        "expected": []
    }
    '''
    line: int
    action: Action
    expected: Tuple[Expected, ...]


class AssertReturnCanonicalNan(NamedTuple):
    '''
    {
        "type": "assert_return_canonical_nan",
        "line": 347,
        "action": {
            "type": "invoke",
            "field": "f64.promote_f32",
            "args": [
                {"type": "f32", "value": "2143289344"}
            ]
        },
        "expected": [
            {"type": "f64"}
        ]
    }
    '''
    line: int
    action: Action
    expected: Tuple[Expected, ...]


class AssertReturnArithmeticNan(NamedTuple):
    '''
    {
        "type": "assert_return_arithmetic_nan",
        "line": 348,
        "action": {
            "type": "invoke",
            "field": "f64.promote_f32",
            "args": [
                {"type": "f32", "value": "2141192192"}
            ]
        },
        "expected": [
            {"type": "f64"}
        ]
    }
    '''
    line: int
    action: Action
    expected: Tuple[Expected, ...]


class AssertUnlinkable(NamedTuple):
    '''
    {
        "type": "assert_unlinkable",
        "line": 162,
        "filename": "data.wast.25.wasm",
        "text": "data segment does not fit",
        "module_type": "binary"
    }
    '''
    line: int
    file_path: Path
    text: str
    module_type: str


class Register(NamedTuple):
    '''
    {
        "type": "register",
        "line": 351,
        "name": "$module1",
        "as": "module1"
    }
    '''
    line: int
    name: Optional[str]
    as_: str


class ActionCommand(NamedTuple):
    '''
    {
        "type": "action",
        "line": 784,
        "action": {
            "type": "invoke",
            "field": "init",
            "args": [
                {"type": "i32", "value": "0"},
                {"type": "f32", "value": "1097963930"}
            ]
        },
        "expected": []
    }
    '''
    line: int
    action: Action
    expected: Tuple[Expected, ...]


class AssertUninstantiable(NamedTuple):
    '''
    {
        "type": "assert_uninstantiable",
        "line": 98,
        "filename": "start.wast.8.wasm",
        "text": "unreachable",
        "module_type": "binary"
    }
    '''
    line: int
    file_path: Path
    text: str
    module_type: str


TCommand = Union[
    ModuleCommand,
    AssertReturnArithmeticNan,
    ActionCommand,
    AssertExhaustion,
    AssertInvalidCommand,
    AssertMalformed,
    AssertReturnArithmeticNan,
    AssertReturnCanonicalNan,
    AssertReturnCommand,
    AssertTrap,
    AssertUninstantiable,
    AssertUnlinkable,
    ModuleCommand,
    Register,
]


class Fixture(NamedTuple):
    file_path: Path
    commands: Tuple[TCommand, ...]
