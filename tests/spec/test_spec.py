import json
from typing import (
    Any,
    Iterable,
    List,
    NamedTuple,
    Optional,
)
from pathlib import Path

import pytest

import wasm


FIXTURES_DIR = Path(__file__).parent / 'fixtures'


class ModuleCommand(NamedTuple):
    line: int
    filename: Path


def normalize_module_command(raw_command):
    return ModuleCommand(
        line=raw_command['line'],
        filename=raw_command['filename']
    )


class ReturnType(NamedTuple):
    type: str
    value: Any


class Action(NamedTuple):
    type: str
    field: str
    args: List[Any]
    expected: Optional[ReturnType]


def normalize_action(raw_action):
    if "expected" in raw_action:
        expected = ReturnType(
            type=raw_action['expected']['type'],
            value=raw_action['expected']['value'],
        )
    else:
        expected = None
    return Action(
        type=raw_action['type'],
        field=raw_action['field'],
        args=raw_action['args'],
        expected=expected,
    )


class AssertReturnCommand(NamedTuple):
    line: int
    action: Action


def normalize_assert_return_command(raw_command):
    return AssertReturnCommand(
        line=raw_command['line'],
        action=normalize_action(raw_command['action']),
    )


class AssertInvalidCommand(NamedTuple):
    line: int
    filename: str
    text: str
    module_type: str


def normalize_assert_invalid(raw_command):
    if raw_command['module_type'] != 'binary':
        raise ValueError(f"Unsupported module_type: {raw_command['module_type']}")

    return AssertInvalidCommand(
        line=raw_command['line'],
        filename=raw_command['filename'],
        text=raw_command['text'],
        module_type=raw_command['module_type'],
    )


def normalize_command(raw_command):
    if raw_command['type'] == 'module':
        return normalize_module_command(raw_command)
    elif raw_command['type'] == 'assert_return':
        return normalize_assert_return_command(raw_command)
    elif raw_command['type'] == 'assert_invalid':
        return normalize_assert_invalid(raw_command)
    else:
        raise Exception(f"Unknown command type: {raw_command['type']}")


def normalize_fixture(raw_fixture):
    filename = raw_fixture["source_filename"]
    commands = tuple(
        normalize_command(raw_command)
        for raw_command in raw_fixture['commands']
    )


@pytest.fixture
def fixture():
    fixture_path = FIXTURES_DIR / "nop.wast.json"
    with open(fixture_path) as fixture_json_file:
        raw_fixture = json.load(fixture_json_file)
    fixture = normalize_fixture(raw_fixture)
    return fixture


def test_json_fixture(fixture):
    store = wasm.init_store()
