import copy
import json
import logging
from pathlib import (
    Path,
)
import time
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Tuple,
    Union,
)

import numpy
import pytest

from wasm import (
    Runtime,
)
from wasm._utils.float import (
    is_arithmetic_nan,
    is_canonical_nan,
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
    arithmetic_nan,
    canonical_nan,
)
from .normalizers import (
    normalize_fixture,
)

logger = logging.getLogger("wasm.tools.fixtures.runner")


CurrentModule = Optional[ModuleInstance]
AllModules = Dict[str, ModuleInstance]


def instantiate_module_from_wasm_file(file_path: Path,
                                      runtime: Runtime) -> ModuleInstance:
    module = runtime.load_module(file_path)
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
    AssertReturnCanonicalNan,
    AssertReturnArithmeticNan,
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
    function_name = action.field.encode('latin1').decode('utf8')

    # get function address
    function_address = None
    for export in module.exports:
        if export.is_function and export.name == function_name:
            function_address = export.function_address
            logger.debug("function_address: %s", function_address)
            break
    else:
        raise Exception(f"No function found by name: {function_name}")

    args = tuple(arg.value for arg in action.args)

    # invoke func
    ret = runtime.invoke_function(function_address, tuple(args))

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


TDoAssertReturnCommands = Union[
    AssertReturnCommand,
    AssertReturnCanonicalNan,
    AssertReturnArithmeticNan,
]


def do_assert_return(command: TDoAssertReturnCommands,
                     module: CurrentModule,
                     all_modules: AllModules,
                     runtime: Runtime) -> None:
    ret = run_opcode_action(command, module, all_modules, runtime)

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
        assert expected_val is not None
        expected_type = expected.valtype
        actual_type = type(actual)

        assert actual_type is expected_type.value

        if expected_val is arithmetic_nan:
            assert is_arithmetic_nan(actual)
        elif expected_val is canonical_nan:
            assert is_canonical_nan(actual)
        elif expected_type.is_integer_type:
            logger.debug("expected: %s | actual: %s", expected_val, actual)
            assert isinstance(actual, (numpy.uint32, numpy.uint64))

            assert actual == expected_val
        elif expected_type.is_float_type:
            assert isinstance(actual, (numpy.float32, numpy.float64))
            assert isinstance(expected_val, (numpy.float32, numpy.float64))

            if numpy.isnan(expected_val):
                assert numpy.isnan(actual)
            else:
                assert expected_val == actual

            assert expected_val.tobytes() == actual.tobytes()
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
        with pytest.raises(Trap):
            run_opcode_action(command, module, all_modules, runtime)
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
    do_assert_return(command, module, all_modules, runtime)


def do_assert_arithmetic_nan(command: AssertReturnArithmeticNan,
                             module: CurrentModule,
                             all_modules: AllModules,
                             runtime: Runtime) -> None:
    do_assert_return(command, module, all_modules, runtime)


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


def run_fixture_test(fixture_path: Path,
                     runtime: Runtime,
                     stop_after: int = None) -> None:
    with fixture_path.open('r') as fixture_file:
        raw_fixture = json.load(fixture_file)

    fixture = normalize_fixture(fixture_path.parent, raw_fixture)

    module = None

    logger.info("Test fixture: %s", fixture.file_path.name)

    all_modules = copy.copy(runtime.modules)

    for idx, command in enumerate(fixture.commands):
        logger.info("command: line=%d  type=%s", command.line, str(type(command)))

        command_fn = get_command_fn(command)

        start_at = time.perf_counter()
        result = command_fn(command, module, all_modules, runtime)
        end_at = time.perf_counter()

        if result:
            module = result
        logger.info(
            "finished command: line=%d  type=%s  took=%f",
            command.line,
            str(type(command)),
            end_at - start_at,
        )

        if stop_after is not None and command.line >= stop_after:
            break

    logger.info("Finished test fixture: %s", fixture.file_path.name)
