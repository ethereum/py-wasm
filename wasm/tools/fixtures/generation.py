from pathlib import (
    Path,
)
from typing import (
    Any,
    Iterable,
    Tuple,
)

from wasm._utils.decorators import (
    to_tuple,
)

from .loading import (
    find_json_fixture_files,
)


#
# Pytest fixture generation
#
def idfn(fixture_path: Path) -> str:
    return str(fixture_path.resolve())


SLOW_FIXTURES = {
    'call.wast.json',
    'call_indirect.wast.json',
    'memory_grow.wast.json',
    'skip-stack-guard-page.wast.json',
}


@to_tuple
def mark_fixtures(all_fixture_paths: Tuple[Path, ...],
                  skip_slow: bool) -> Iterable[Path]:
    import pytest

    for fixture_path in sorted(all_fixture_paths):
        if skip_slow and fixture_path.name in SLOW_FIXTURES:
            yield pytest.param(fixture_path, marks=pytest.mark.skip("slow"))
        else:
            yield fixture_path


def generate_fixture_tests(metafunc: Any,
                           fixtures_dir: Path,
                           skip_slow: bool) -> None:
    """
    Helper function for use with `pytest_generate_tests` to generate fixture tests.

    - `metafunc` is the parameter from `pytest_generate_tests`
    - `fixtures_dir` is the base path that fixture files will be collected from.
    """
    if 'fixture_path' in metafunc.fixturenames:
        all_fixture_paths = mark_fixtures(
            all_fixture_paths=find_json_fixture_files(fixtures_dir),
            skip_slow=skip_slow,
        )
        if len(all_fixture_paths) == 0:
            raise Exception("Invariant: found zero fixtures")

        metafunc.parametrize('fixture_path', all_fixture_paths, ids=idfn)
