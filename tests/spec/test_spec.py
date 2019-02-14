from pathlib import (
    Path,
)

import numpy

from wasm import (
    Runtime,
)
from wasm.tools import (
    generate_fixture_tests,
    instantiate_spectest_module,
    instantiate_test_module,
    run_fixture_test,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def pytest_generate_tests(metafunc):
    skip_slow_spec = metafunc.config.getoption('skip_slow_spec')
    generate_fixture_tests(
        metafunc=metafunc,
        fixtures_dir=FIXTURES_DIR,
        skip_slow=skip_slow_spec,
    )


def test_json_fixture(fixture_path, pytestconfig):
    # ensure that all numpy flags are set to raise exceptions
    numpy.seterr(all='raise')

    stop_after_command_line = pytestconfig.getoption('stop_after_command_line')
    runtime = Runtime()
    # module "spectest" is imported from by many tests
    runtime.register_module(
        "spectest",
        instantiate_spectest_module(runtime.store),
    )
    # module "test" is imported from by many tests
    runtime.register_module(
        "test",
        instantiate_test_module(runtime.store),
    )
    run_fixture_test(fixture_path, runtime, stop_after_command_line)
