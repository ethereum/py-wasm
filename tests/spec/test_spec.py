from pathlib import (
    Path,
)

import wasm
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
    store = wasm.init_store()
    modules = {
        "spectest": instantiate_spectest_module(
            store
        ),  # module "spectest" is imported from by many tests
        "test": instantiate_test_module(
            store
        ),  # module "test" is imported from by many tests
    }
    registered_modules = {
        "spectest": modules["spectest"],  # register module "spectest" to be import-able
        "test": modules["test"],  # register module "test" to be import-able
    }
    run_fixture_test(fixture_path, store, modules, registered_modules)
