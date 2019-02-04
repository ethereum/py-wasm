from pathlib import (
    Path,
)

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
    generate_fixture_tests(
        metafunc=metafunc,
        fixtures_dir=FIXTURES_DIR,
    )


def test_json_fixture(fixture_path):
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
    run_fixture_test(fixture_path, runtime)
