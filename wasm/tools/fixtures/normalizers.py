from pathlib import (
    Path,
)
from typing import (
    Dict,
    Union,
)

from wasm import (
    constants,
)

from .datatypes import (
    Action,
    ActionCommand,
    Argument,
    AssertExhaustion,
    AssertInvalidCommand,
    AssertMalformed,
    AssertReturnArithmeticNan,
    AssertReturnCanonicalNan,
    AssertReturnCommand,
    AssertTrap,
    AssertUninstantiable,
    AssertUnlinkable,
    Expected,
    Fixture,
    ModuleCommand,
    Register,
)
from .numeric import (
    int_to_float,
)


class empty:
    pass


def normalize_module_command(raw_command: Dict[str, Union[int, str]],
                             base_fixtures_dir) -> ModuleCommand:
    expected_keys = {'type', 'line', 'filename', 'name'}
    extra_keys = set(raw_command.keys()).difference(expected_keys)
    if extra_keys:
        raise Exception(f"Unexpected keys: {extra_keys}")

    file_path = base_fixtures_dir / raw_command['filename']

    return ModuleCommand(
        line=raw_command['line'],
        file_path=file_path,
        name=raw_command.get('name'),
    )


def normalize_argument(raw_argument: Dict[str, str]) -> Argument:
    expected_keys = {'type', 'value'}
    extra_keys = set(raw_argument.keys()).difference(expected_keys)
    if extra_keys:
        raise Exception(f"Unexpected keys: {extra_keys}")

    _type = raw_argument['type']

    if _type in constants.INTEGER_TYPES:
        value = int(raw_argument['value'])
    elif _type == constants.F32:
        value = int_to_float(32, int(raw_argument['value']))
    elif _type == constants.F64:
        value = int_to_float(64, int(raw_argument['value']))
    else:
        raise Exception(f"Unhandled type: {_type} | value: {raw_argument['value']}")

    return Argument(
        type=_type,
        value=value,
    )


def normalize_action(raw_action: Dict[str, str]) -> Action:
    expected_keys = {'type', 'field', 'args', 'module'}
    extra_keys = set(raw_action.keys()).difference(expected_keys)
    if extra_keys:
        raise Exception(f"Unexpected keys: {extra_keys}")

    if raw_action['type'] == 'invoke':
        return _normalize_invoke_action(raw_action)
    elif raw_action['type'] == 'get':
        return _normalize_get_action(raw_action)
    else:
        raise Exception(f"Unhandled action type: {raw_action['type']}")


def _normalize_get_action(raw_action: Dict[str, str]) -> Action:
    if 'args' in raw_action:
        raise Exception("Unhandled")
    return Action(
        type=raw_action['type'],
        field=raw_action['field'],
        module=raw_action.get('module'),
        args=None,
    )


def _normalize_invoke_action(raw_action: Dict[str, str]) -> Action:
    return Action(
        type=raw_action['type'],
        field=raw_action['field'],
        module=raw_action.get('module'),
        args=tuple(
            normalize_argument(raw_argument)
            for raw_argument in raw_action['args']
        ),
    )


def normalize_expected(raw_expected: Dict[str, str]) -> Expected:
    expected_keys = {'type', 'value'}
    extra_keys = set(raw_expected.keys()).difference(expected_keys)
    if extra_keys:
        raise Exception(f"Unexpected keys: {extra_keys}")

    _type = raw_expected['type']

    if 'value' in raw_expected:
        if _type in constants.INTEGER_TYPES:
            value = int(raw_expected['value'])
        elif _type == constants.F32:
            value = int_to_float(32, int(raw_expected['value']))
        elif _type == constants.F64:
            value = int_to_float(64, int(raw_expected['value']))
        else:
            raise Exception(f"Unhandled type: {_type} | value: {raw_expected['value']}")
    else:
        value = None

    return Expected(
        type=_type,
        value=value,
    )


def normalize_assert_return_command(raw_command, base_fixtures_dir):
    expected_keys = {'type', 'line', 'action', 'expected'}
    extra_keys = set(raw_command.keys()).difference(expected_keys)
    if extra_keys:
        raise Exception(f"Unexpected keys: {extra_keys}")

    return AssertReturnCommand(
        line=raw_command['line'],
        action=normalize_action(raw_command['action']),
        expected=tuple(
            normalize_expected(raw_expected)
            for raw_expected
            in raw_command['expected']
        ),
    )


def normalize_assert_return_canonical_nan(raw_command):
    return _normalize_assert_return_common_nan(
        raw_command,
        AssertReturnCanonicalNan,
    )


def normalize_assert_return_arithmetic_nan(raw_command):
    return _normalize_assert_return_common_nan(
        raw_command,
        AssertReturnArithmeticNan
    )


def _normalize_assert_return_common_nan(raw_command, normalized_type):
    expected_keys = {'type', 'line', 'action', 'expected'}
    extra_keys = set(raw_command.keys()).difference(expected_keys)
    if extra_keys:
        raise Exception(f"Unexpected keys: {extra_keys}")

    return normalized_type(
        line=raw_command['line'],
        action=normalize_action(raw_command['action']),
        expected=tuple(
            normalize_expected(raw_expected)
            for raw_expected
            in raw_command['expected']
        ),
    )


def normalize_assert_invalid(raw_command, base_fixtures_dir):
    expected_keys = {'type', 'line', 'filename', 'text', 'module_type'}
    extra_keys = set(raw_command.keys()).difference(expected_keys)
    if extra_keys:
        raise Exception(f"Unexpected keys: {extra_keys}")

    if raw_command['module_type'] != 'binary':
        raise ValueError(f"Unsupported module_type: {raw_command['module_type']}")

    file_path = base_fixtures_dir / raw_command['filename']

    return AssertInvalidCommand(
        line=raw_command['line'],
        file_path=file_path,
        text=raw_command['text'],
        module_type=raw_command['module_type'],
    )


def normalize_assert_trap(raw_command):
    expected_keys = {'type', 'line', 'action', 'text', 'expected'}
    extra_keys = set(raw_command.keys()).difference(expected_keys)
    if extra_keys:
        raise Exception(f"Unexpected keys: {extra_keys}")

    return AssertTrap(
        line=raw_command['line'],
        action=normalize_action(raw_command['action']),
        text=raw_command['text'],
        expected=tuple(
            normalize_expected(raw_expected)
            for raw_expected in raw_command['expected']
        ),
    )


def normalize_assert_malformed(raw_command, base_fixtures_dir: Path):
    expected_keys = {'type', 'line', 'filename', 'text', 'module_type'}
    extra_keys = set(raw_command.keys()).difference(expected_keys)
    if extra_keys:
        raise Exception(f"Unexpected keys: {extra_keys}")

    return AssertMalformed(
        line=raw_command['line'],
        file_path=base_fixtures_dir / raw_command['filename'],
        text=raw_command['text'],
        module_type=raw_command['module_type'],
    )


def normalize_assert_exhaustion(raw_command):
    expected_keys = {'type', 'line', 'action', 'expected'}
    extra_keys = set(raw_command.keys()).difference(expected_keys)
    if extra_keys:
        raise Exception(f"Unexpected keys: {extra_keys}")

    return AssertExhaustion(
        line=raw_command['line'],
        action=normalize_action(raw_command['action']),
        expected=tuple(
            normalize_expected(raw_expected)
            for raw_expected in raw_command['expected']
        ),
    )


def normalize_assert_unlinkable(raw_command, base_fixtures_dir):
    expected_keys = {'type', 'line', 'filename', 'text', 'module_type'}
    extra_keys = set(raw_command.keys()).difference(expected_keys)
    if extra_keys:
        raise Exception(f"Unexpected keys: {extra_keys}")

    if raw_command['module_type'] != 'binary':
        raise ValueError(f"Unsupported module_type: {raw_command['module_type']}")

    return AssertUnlinkable(
        line=raw_command['line'],
        file_path=base_fixtures_dir / raw_command['filename'],
        text=raw_command['text'],
        module_type=raw_command['module_type'],
    )


def normalize_register(raw_command):
    expected_keys = {'type', 'line', 'name', 'as'}
    extra_keys = set(raw_command.keys()).difference(expected_keys)
    if extra_keys:
        raise Exception(f"Unexpected keys: {extra_keys}")

    return Register(
        line=raw_command['line'],
        name=raw_command.get('name'),
        as_=raw_command['as'],
    )


def normalize_action_command(raw_command):
    expected_keys = {'type', 'line', 'action', 'expected'}
    extra_keys = set(raw_command.keys()).difference(expected_keys)
    if extra_keys:
        raise Exception(f"Unexpected keys: {extra_keys}")

    return ActionCommand(
        line=raw_command['line'],
        action=normalize_action(raw_command['action']),
        expected=tuple(
            normalize_expected(raw_expected)
            for raw_expected in raw_command['expected']
        ),
    )


def normalize_assert_uninstantiable(raw_command, base_fixtures_dir):
    expected_keys = {'type', 'line', 'filename', 'text', 'module_type'}
    extra_keys = set(raw_command.keys()).difference(expected_keys)
    if extra_keys:
        raise Exception(f"Unexpected keys: {extra_keys}")

    if raw_command['module_type'] != 'binary':
        raise ValueError(f"Unsupported module_type: {raw_command['module_type']}")

    return AssertUninstantiable(
        line=raw_command['line'],
        file_path=base_fixtures_dir / raw_command['filename'],
        text=raw_command['text'],
        module_type=raw_command['module_type'],
    )


def normalize_command(raw_command, base_fixtures_dir: Path):
    if raw_command['type'] == 'module':
        return normalize_module_command(raw_command, base_fixtures_dir)
    elif raw_command['type'] == 'assert_return':
        return normalize_assert_return_command(raw_command, base_fixtures_dir)
    elif raw_command['type'] == 'assert_invalid':
        return normalize_assert_invalid(raw_command, base_fixtures_dir)
    elif raw_command['type'] == 'assert_trap':
        return normalize_assert_trap(raw_command)
    elif raw_command['type'] == 'assert_malformed':
        return normalize_assert_malformed(raw_command, base_fixtures_dir)
    elif raw_command['type'] == 'assert_exhaustion':
        return normalize_assert_exhaustion(raw_command)
    elif raw_command['type'] == 'assert_return_canonical_nan':
        return normalize_assert_return_canonical_nan(raw_command)
    elif raw_command['type'] == 'assert_return_arithmetic_nan':
        return normalize_assert_return_arithmetic_nan(raw_command)
    elif raw_command['type'] == 'assert_unlinkable':
        return normalize_assert_unlinkable(raw_command, base_fixtures_dir)
    elif raw_command['type'] == 'register':
        return normalize_register(raw_command)
    elif raw_command['type'] == 'action':
        return normalize_action_command(raw_command)
    elif raw_command['type'] == 'assert_uninstantiable':
        return normalize_assert_uninstantiable(raw_command, base_fixtures_dir)
    else:
        raise Exception(f"Unknown command type: {raw_command['type']}")


def normalize_fixture(base_fixtures_dir, raw_fixture):
    file_path = base_fixtures_dir / raw_fixture["source_filename"]
    commands = tuple(
        normalize_command(raw_command, base_fixtures_dir)
        for raw_command in raw_fixture['commands']
    )
    return Fixture(
        file_path=file_path,
        commands=commands,
    )
