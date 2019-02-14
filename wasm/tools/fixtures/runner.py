import copy
import json
import logging
import math
from pathlib import (
    Path,
)
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Tuple,
    Type,
    Union,
)

import pytest

import wasm
from wasm import (
    Runtime,
)
from wasm.datatypes import (
    ModuleInstance,
)
from wasm.exceptions import (
    Exhaustion,
    InvalidModule,
    MalformedModule,
    Trap,
    Unlinkable,
)
from wasm.typing import (
    TValue,
)

from .datatypes import (
    Action,
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


CurrentModule = Optional[ModuleInstance]
AllModules = Dict[str, ModuleInstance]


def instantiate_module_from_wasm_file(file_path: Path,
                                      runtime: Runtime) -> ModuleInstance:
    logger.debug("Loading wasm module from file: %s", file_path.name)

    if file_path.suffix != ".wasm":
        logger.debug("Unsupported file type for wasm module: %s", file_path.suffix)
        raise Exception("Unsupported file type: {file_path.suffix}")

    with file_path.open("rb") as wasm_module_file:
        # memoryview doesn't make copy, bytearray may require copy
        wasmbytes = memoryview(wasm_module_file.read())
        module = wasm.decode_module(wasmbytes)

    wasm.validate_module(module)

    module_instance, _ = runtime.instantiate_module(module)

    return module_instance


def do_module(command: ModuleCommand,
              module: CurrentModule,
              all_modules: AllModules,
              runtime: Runtime) -> ModuleInstance:
    if command.file_path is not None:
        module = instantiate_module_from_wasm_file(command.file_path, runtime)

        if command.name is not None:
            all_modules[command.name] = module

        return module
    else:
        raise Exception("Unhandled")


TActionCommands = Union[
    AssertReturnCommand,
    AssertTrap,
    AssertExhaustion,
]
TAnyCommand = Union[
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


def run_opcode_action(command: TActionCommands,
                      module: CurrentModule,
                      all_modules: AllModules,
                      runtime: Runtime) -> Tuple[TValue, ...]:
    if command.action.module is not None:
        module = all_modules[command.action.module]

    if module is None:
        raise Exception("Invariant")

    if command.action.type == "invoke":
        ret = run_opcode_action_invoke(
            command.action, module, all_modules, runtime,
        )
    elif command.action.type == "get":
        ret = run_opcode_action_get(
            command.action, module, all_modules, runtime,
        )
    else:
        raise Exception(f"Unsupported action type: {command.action.type}")

    return ret


def run_opcode_action_invoke(action: Action,
                             module: ModuleInstance,
                             all_modules: AllModules,
                             runtime: Runtime) -> Tuple[TValue, ...]:
    # get function name, which could include unicode bytes like \u001b which
    # must be converted to unicode string
    funcname = action.field.encode('latin1').decode('utf8')

    # get function address
    funcaddr = None
    for export in module.exports:
        if export.is_function and export.name == funcname:
            funcaddr = export.value
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
        args.append((type_, value))

    # invoke func
    _, ret = wasm.invoke_func(runtime.store, funcaddr, tuple(args))

    return ret


def run_opcode_action_get(action: Action,
                          module: ModuleInstance,
                          all_modules: AllModules,
                          runtime: Runtime) -> Tuple[TValue, ...]:
    # this is naive, since test["expected"] is a list, should iterate over each
    # one, but maybe OK since there is only one test["action"]
    for export in module.exports:
        if export.name == action.field:
            globaladdr = export.value
            value = runtime.store.globals[globaladdr].value
            return (value,)
    else:
        raise Exception(f"No export found for name: '{action.field}")


def do_assert_return(command: AssertReturnCommand,
                     module: CurrentModule,
                     all_modules: AllModules,
                     runtime: Runtime) -> None:
    try:
        ret = run_opcode_action(command, module, all_modules, runtime)
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


def do_assert_invalid(command: AssertInvalidCommand,
                      module: CurrentModule,
                      all_modules: AllModules,
                      runtime: Runtime) -> None:
    if command.module_type != "binary":
        raise Exception("Unhandled")

    if command.file_path:
        with pytest.raises(InvalidModule):
            instantiate_module_from_wasm_file(command.file_path, runtime)
    else:
        raise Exception("Unhandled")


def do_assert_trap(command: AssertTrap,
                   module: CurrentModule,
                   all_modules: AllModules,
                   runtime: Runtime) -> None:
    if hasattr(command, 'module'):
        raise Exception("Unhandled")

    if command.action:
        try:
            with pytest.raises(Trap):
                run_opcode_action(command, module, all_modules, runtime)
        except FloatingPointNotImplemented:
            pass
    else:
        raise Exception("Unhandled")


def do_assert_malformed(command: AssertMalformed,
                        module: CurrentModule,
                        all_modules: AllModules,
                        runtime: Runtime) -> None:
    if command.module_type == 'text':
        assert not command.file_path.exists()
        logger.info("Skipping command for text_module")
        return
    elif command.module_type != 'binary':
        raise Exception("Unhandled")

    if command.file_path:
        with pytest.raises(MalformedModule):
            instantiate_module_from_wasm_file(command.file_path, runtime)
    else:
        raise Exception("Unhandled")


def do_assert_exhaustion(command: AssertExhaustion,
                         module: CurrentModule,
                         all_modules: AllModules,
                         runtime: Runtime) -> None:
    if hasattr(command, 'module'):
        raise Exception("Unhandled")

    if command.action:
        with pytest.raises(Exhaustion):
            run_opcode_action(command, module, all_modules, runtime)
    else:
        raise Exception("Unhandled")


def do_assert_canonical_nan(command: AssertReturnCanonicalNan,
                            module: CurrentModule,
                            all_modules: AllModules,
                            runtime: Runtime) -> None:
    # Not yet implemented
    pass


def do_assert_arithmetic_nan(command: AssertReturnArithmeticNan,
                             module: CurrentModule,
                             all_modules: AllModules,
                             runtime: Runtime) -> None:
    # Not yet implemented
    pass


def do_assert_unlinkable(command: AssertUnlinkable,
                         module: CurrentModule,
                         all_modules: AllModules,
                         runtime: Runtime) -> None:
    if command.module_type == 'text':
        assert not command.file_path.exists()
        logger.info("Skipping command for text_module")
        return
    elif command.module_type != 'binary':
        raise Exception("Unhandled")

    if command.file_path:
        with pytest.raises(Unlinkable):
            instantiate_module_from_wasm_file(command.file_path, runtime)
    else:
        raise Exception("Unhandled")


def do_register(command: Register,
                module: CurrentModule,
                all_modules: AllModules,
                runtime: Runtime) -> None:
    if command.name is None:
        if module is None:
            raise Exception("Invariant")
        runtime.register_module(command.as_, module)
    else:
        runtime.register_module(command.as_, all_modules[command.name])


def do_assert_uninstantiable(command: AssertUninstantiable,
                             module: CurrentModule,
                             all_modules: AllModules,
                             runtime: Runtime) -> None:
    with pytest.raises(Trap):
        instantiate_module_from_wasm_file(command.file_path, runtime)


CommandFn = Callable[
    [TAnyCommand, CurrentModule, AllModules, Runtime],
    Any,
]


def get_command_fn(command: TAnyCommand) -> CommandFn:
    if isinstance(command, ModuleCommand):
        return do_module  # type: ignore
    elif isinstance(command, AssertReturnCommand):
        return do_assert_return  # type: ignore
    elif isinstance(command, AssertInvalidCommand):
        return do_assert_invalid  # type: ignore
    elif isinstance(command, AssertExhaustion):
        return do_assert_exhaustion  # type: ignore
    elif isinstance(command, AssertMalformed):
        return do_assert_malformed  # type: ignore
    elif isinstance(command, AssertTrap):
        return do_assert_trap  # type: ignore
    elif isinstance(command, AssertReturnCanonicalNan):
        return do_assert_canonical_nan  # type: ignore
    elif isinstance(command, AssertReturnArithmeticNan):
        return do_assert_arithmetic_nan  # type: ignore
    elif isinstance(command, AssertUnlinkable):
        return do_assert_unlinkable  # type: ignore
    elif isinstance(command, Register):
        return do_register  # type: ignore
    elif isinstance(command, ActionCommand):
        return run_opcode_action  # type: ignore
    elif isinstance(command, AssertUninstantiable):
        return do_assert_uninstantiable  # type: ignore
    else:
        raise AssertionError(f"Unsupported module type: {type(command)}")


# This data structure holds all of the tests from the WASM spec tests that are
# currently not passing.  This list should be empty once the library has been
# properly refactored but for now they are skipped to allow for incremental
# improvement to the library.
SKIP_COMMANDS: Dict[str, Dict[int, Type[Exception]]] = {
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


def run_fixture_test(fixture_path: Path,
                     runtime: Runtime,
                     stop_after: int = None) -> None:
    with fixture_path.open('r') as fixture_file:
        raw_fixture = json.load(fixture_file)

    fixture = normalize_fixture(fixture_path.parent, raw_fixture)

    module = None
    skip_info = SKIP_COMMANDS.get(fixture.file_path.name, {})

    logger.info("Finished test fixture: %s", fixture.file_path.name)

    all_modules = copy.copy(runtime.modules)

    for idx, command in enumerate(fixture.commands):
        logger.debug("running command: line=%d  type=%s", command.line, str(type(command)))

        command_fn = get_command_fn(command)

        if command.line in skip_info:
            expected_err = skip_info[command.line]
            with pytest.raises(expected_err):
                command_fn(command, module, all_modules, runtime)
        else:
            result = command_fn(command, module, all_modules, runtime)

            if result:
                module = result
        logger.debug("Finished command: line=%d  type=%s", command.line, str(type(command)))

        if stop_after is not None and command.line >= stop_after:
            break

    logger.debug("Finished test fixture: %s", fixture.file_path.name)
