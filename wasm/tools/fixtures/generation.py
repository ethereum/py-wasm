from pathlib import (
    Path,
)
from typing import (
    Any,
)

from .loading import (
    find_json_fixture_files,
)


#
# Pytest fixture generation
#
def idfn(fixture_path: Path) -> str:
    return str(fixture_path.resolve())


def generate_fixture_tests(metafunc: Any,
                           fixtures_dir: Path) -> None:
    """
    Helper function for use with `pytest_generate_tests` to generate fixture tests.

    - `metafunc` is the parameter from `pytest_generate_tests`
    - `fixtures_dir` is the base path that fixture files will be collected from.
    """
    if 'fixture_path' in metafunc.fixturenames:
        all_fixture_paths = tuple(sorted(find_json_fixture_files(fixtures_dir)))
        if len(all_fixture_paths) == 0:
            raise Exception("Invariant: found zero fixtures")

        metafunc.parametrize('fixture_path', all_fixture_paths, ids=idfn)
