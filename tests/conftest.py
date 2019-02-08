def pytest_addoption(parser):
    parser.addoption("--skip-slow-spec", action="store_true", required=False)
