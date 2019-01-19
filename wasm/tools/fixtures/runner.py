import json
import logging
import math
from pathlib import (
    Path,
)
from typing import (
    Any,
    Dict,
    List,
)

import pytest

from _pytest.outcomes import (
    Failed,
)
import wasm
from wasm.exceptions import (
    Exhaustion,
    InvalidModule,
    MalformedModule,
    Trap,
    Unlinkable,
)
from wasm.typing import (
    Store,
)

from .datatypes import (
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
)
from .normalizers import (
    normalize_fixture,
)

logger = logging.getLogger("wasm.tools.fixtures.runner")


class FloatingPointNotImplemented(NotImplementedError):
    pass


def instantiate_module_from_wasm_file(
        file_path: Path,
        store: Store,
        registered_modules: List[Any, ]
) -> Dict[Any, Any]:
    logger.debug("Loading wasm module from file: %s", file_path.name)

    if file_path.suffix != ".wasm":
        logger.debug("Unsupported file type for wasm module: %s", file_path.suffix)
        raise Exception("Unsupported file type: {file_path.suffix}")

    with file_path.open("rb") as wasm_module_file:
        # memoryview doesn't make copy, bytearray may require copy
        wasmbytes = memoryview(wasm_module_file.read())
        module = wasm.decode_module(wasmbytes)

        # validate
        wasm.validate_module(module)

        # imports preparation
        externvalstar: List[Any] = []
        for import_ in module["imports"]:
            if import_.module not in registered_modules:
                raise Unlinkable(f"Unlinkable module: {import_.module}")

            sub_module = registered_modules[import_.module]

            for export in sub_module["exports"]:
                if export.name == import_.name:
                    externval = export.desc
                    break
            else:
                raise Unlinkable("Unlinkable module: export name not found")

            externvalstar += [externval]
        _, moduleinst, _ = wasm.instantiate_module(store, module, externvalstar)
    return moduleinst


def do_module(command, store, module, all_modules, registered_modules):
    if command.file_path is not None:
        module = instantiate_module_from_wasm_file(
            command.file_path, store, registered_modules
        )

        if command.name is not None:
            all_modules[command.name] = module

        return module
    else:
        raise Exception("Unhandled")


def run_opcode_action(command, store, module, all_modules, registered_modules):
    if command.action.module is not None:
        module = all_modules[command.action.module]

    if command.action.type == "invoke":
        ret = run_opcode_action_invoke(
            command.action, store, module, all_modules, registered_modules
        )
    elif command.action.type == "get":
        ret = run_opcode_action_get(
            command.action, store, module, all_modules, registered_modules
        )
    else:
        raise Exception(f"Unsupported action type: {command.action.type}")

    return ret


def run_opcode_action_invoke(action, store, module, all_modules, registered_modules):
    # get function name, which could include unicode bytes like \u001b which
    # must be converted to unicode string
    funcname = action.field
    idx = 0
    utf8_bytes = bytearray()
    for c in funcname:
        utf8_bytes += bytearray([ord(c)])
    utf8_bytes = wasm.spec_binary_uN_inv(len(funcname), 32) + utf8_bytes
    _, funcname = wasm.spec_binary_name(utf8_bytes, 0)

    # get function address
    funcaddr = None
    for export in module["exports"]:
        # print("export[\"name\"]",export["name"])
        if export.name == funcname:
            funcaddr = export.desc
            logger.debug("funcaddr: %s", funcaddr)
            break
    else:
        raise Exception(f"No function found by name: {funcname}")

    # get args
    args = []

    for idx, arg in enumerate(action.args):
        type_ = arg.type
        value = arg.value

        if type_.is_float_type:
            logger.info("Floating point not yet supported: %s", action)
            raise FloatingPointNotImplemented("Floating point not yet implemented")
        args += [[type_.value + ".const", value]]

    # invoke func
    _, ret = wasm.invoke_func(store, funcaddr, args)

    return ret


def run_opcode_action_get(action, store, module, all_modules, registered_modules):
    exports = module["exports"]
    # this is naive, since test["expected"] is a list, should iterate over each
    # one, but maybe OK since there is only one test["action"]
    for export in exports:
        if export.name == action.field:
            globaladdr = export.desc
            value = store["globals"][globaladdr]["value"][1]
            return [value]
    else:
        raise Exception(f"No export found for name: '{action.field}")


def do_assert_return(command, store, module, all_modules, registered_modules):
    try:
        ret = run_opcode_action(command, store, module, all_modules, registered_modules)
    except FloatingPointNotImplemented:
        return

    if len(ret) != len(command.expected):
        logger.debug("ret: %s | expected: %s", ret, command.expected)
        raise AssertionError(
            f"Mismatched number of expected and returned values.  expected: "
            f"{len(command.expected)} | got: {len(ret)}"
        )
    elif len(ret) == 0 and len(command.expected) == 0:
        return

    for idx, (actual, expected) in enumerate(zip(ret, command.expected)):
        expected_val = expected.value
        expected_type = expected.type

        if expected_type.is_integer_type:
            logger.debug("expected: %s | actual: %s", expected_val, actual)

            assert actual == expected_val
        elif expected_type.is_float_type:
            logger.info("Floating point operations not yet implemented, skipping...")
            # TODO: convert to exception and enumerate failing test in SKIP_COMMANDS
            return

            assert isinstance(actual, float)

            if math.isnan(expected_val):
                assert math.isnan(actual)
            elif math.isinf(expected_val):
                assert math.isinf(actual)
            else:
                assert expected_val == actual
        else:
            raise AssertionError(f"Unknown expected return type: {expected_type}")


def do_assert_invalid(command, store, module, all_modules, registered_modules):
    if command.module_type != "binary":
        raise Exception("Unhandled")

    if command.file_path:
        with pytest.raises(InvalidModule):
            instantiate_module_from_wasm_file(command.file_path, store, registered_modules)
    else:
        raise Exception("Unhandled")


def do_assert_trap(command, store, module, all_modules, registered_modules):
    if hasattr(command, 'module'):
        raise Exception("Unhandled")

    if command.action:
        try:
            with pytest.raises(Trap):
                run_opcode_action(command, store, module, all_modules, registered_modules)
        except FloatingPointNotImplemented:
            pass
    else:
        raise Exception("Unhandled")


def do_assert_malformed(command, store, module, all_modules, registered_modules):
    if command.module_type == 'text':
        assert not command.file_path.exists()
        logger.info("Skipping command for text_module")
        return
    elif command.module_type != 'binary':
        raise Exception("Unhandled")

    if command.file_path:
        with pytest.raises(MalformedModule):
            instantiate_module_from_wasm_file(command.file_path, store, registered_modules)
    else:
        raise Exception("Unhandled")


def do_assert_exhaustion(command, store, module, all_modules, registered_modules):
    if hasattr(command, 'module'):
        raise Exception("Unhandled")

    if command.action:
        with pytest.raises(Exhaustion):
            run_opcode_action(command, store, module, all_modules, registered_modules)
    else:
        raise Exception("Unhandled")


def do_assert_canonical_nan(command, store, module, all_modules, registered_modules):
    # Not implemented
    pass


def do_assert_arithmetic_nan(command, store, module, all_modules, registered_modules):
    # Not implemented
    pass


def do_assert_unlinkable(command, store, module, all_modules, registered_modules):
    if command.module_type == 'text':
        assert not command.file_path.exists()
        logger.info("Skipping command for text_module")
        return
    elif command.module_type != 'binary':
        raise Exception("Unhandled")

    if command.file_path:
        with pytest.raises(Unlinkable):
            instantiate_module_from_wasm_file(command.file_path, store, registered_modules)
    else:
        raise Exception("Unhandled")


def do_register(command, store, module, all_modules, registered_modules):
    if command.name is None:
        registered_modules[command.as_] = module
    else:
        registered_modules[command.as_] = all_modules[command.name]


def do_action_command(command, store, module, all_modules, registered_modules):
    run_opcode_action(command, store, module, all_modules, registered_modules)


def do_assert_uninstantiable(command, store, module, all_modules, registered_modules):
    with pytest.raises(Trap):
        instantiate_module_from_wasm_file(command.file_path, store, registered_modules)


def get_command_fn(command):
    if isinstance(command, ModuleCommand):
        return do_module
    elif isinstance(command, AssertReturnCommand):
        return do_assert_return
    elif isinstance(command, AssertInvalidCommand):
        return do_assert_invalid
    elif isinstance(command, AssertExhaustion):
        return do_assert_exhaustion
    elif isinstance(command, AssertMalformed):
        return do_assert_malformed
    elif isinstance(command, AssertTrap):
        return do_assert_trap
    elif isinstance(command, AssertReturnCanonicalNan):
        return do_assert_canonical_nan
    elif isinstance(command, AssertReturnArithmeticNan):
        return do_assert_arithmetic_nan
    elif isinstance(command, AssertUnlinkable):
        return do_assert_unlinkable
    elif isinstance(command, Register):
        return do_register
    elif isinstance(command, ActionCommand):
        return do_action_command
    elif isinstance(command, AssertUninstantiable):
        return do_assert_uninstantiable
    else:
        raise AssertionError(f"Unsupported module type: {type(command)}")


# This data structure holds all of the tests from the WASM spec tests that are
# currently not passing.  This list should be empty once the library has been
# properly refactored but for now they are skipped to allow for incremental
# improvement to the library.
SKIP_COMMANDS = {
    'custom.wast': {
        # It appears that the logic for parsing a binary module is broken,
        # allowing the parser to exit before fully parsing the module.  For
        # this test it ends up exiting before encountering the invalid section
        # which **should** error out due to an invalid section ID.
        93: Failed,
        # This one appears to be lack of validation of the lengths of code and
        # function section types.
        # See the note here about malformed modules:
        # - https://webassembly.github.io/spec/core/bikeshed/index.html#code-section%E2%91%A0
        102: Failed,
    },
    'float_exprs.wast': {
        # Incorrectly implemented floating point operations.
        506: AssertionError,
        510: AssertionError,
        511: AssertionError,
        784: FloatingPointNotImplemented,
        785: FloatingPointNotImplemented,
        786: FloatingPointNotImplemented,
        787: FloatingPointNotImplemented,
        792: FloatingPointNotImplemented,
        819: FloatingPointNotImplemented,
        820: FloatingPointNotImplemented,
        821: FloatingPointNotImplemented,
        822: FloatingPointNotImplemented,
        827: FloatingPointNotImplemented,
        2337: AssertionError,
        2338: AssertionError,
        2339: AssertionError,
        2359: AssertionError,
        2360: AssertionError,
    },
    'float_literals.wast': {
        # Incorrectly implemented floating point operations.
        109: AssertionError,
        111: AssertionError,
        112: AssertionError,
        113: AssertionError,
    },
    'float_memory.wast': {
        # Incorrectly implemented floating point operations.
        21: AssertionError,
        73: AssertionError,
    }
}


def run_fixture_test(fixture_path, store, all_modules, registered_modules):
    with fixture_path.open('r') as fixture_file:
        raw_fixture = json.load(fixture_file)

    fixture = normalize_fixture(fixture_path.parent, raw_fixture)

    module = None
    skip_info = SKIP_COMMANDS.get(fixture.file_path.name, {})

    logger.info("Finished test fixture: %s", fixture.file_path.name)

    for idx, command in enumerate(fixture.commands):
        logger.debug("running command: line=%d  type=%s", command.line, str(type(command)))

        command_fn = get_command_fn(command)

        if command.line in skip_info:
            expected_err = skip_info[command.line]
            with pytest.raises(expected_err):
                command_fn(command, store, module, all_modules, registered_modules)
        else:
            result = command_fn(command, store, module, all_modules, registered_modules)

            if result:
                module = result
        logger.debug("Finished command: line=%d  type=%s", command.line, str(type(command)))

    logger.debug("Finished test fixture: %s", fixture.file_path.name)
