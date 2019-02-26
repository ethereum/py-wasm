import pytest

from wasm.execution.configuration import (
    BaseConfiguration,
    Configuration,
)


def pytest_addoption(parser):
    parser.addoption("--skip-slow-spec", action="store_true", required=False)
    parser.addoption("--stop-after-command-line", type=int, required=False)


@pytest.fixture(autouse=True)
def _enable_logic_function_logging(monkeypatch):
    monkeypatch.setattr(
        BaseConfiguration,
        'enable_logic_fn_logging',
        True,
    )
    monkeypatch.setattr(
        Configuration,
        'enable_logic_fn_logging',
        True,
    )
