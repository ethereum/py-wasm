from pathlib import Path
from typing import (
    Tuple,
)

from wasm.text.grammar import (
    parse,
)


BASE_DIR = Path(__file__).parent.parent.parent.parent
FIXTURES_DIR = BASE_DIR / "spec" / "test" / "core"


def find_wast_fixture_files(fixtures_base_dir: Path) -> Tuple[Path, ...]:
    all_fixture_paths = tuple(fixtures_base_dir.glob('**/*.wast'))
    return all_fixture_paths


def idfn(fixture_path: Path) -> str:
    return str(fixture_path.resolve())


def pytest_generate_tests(metafunc):
    all_fixture_paths = find_wast_fixture_files(FIXTURES_DIR)

    if len(all_fixture_paths) == 0:
        raise Exception("Invariant: found zero fixtures")

    metafunc.parametrize('fixture_path', all_fixture_paths, ids=idfn)


def test_base_sexpression_parser(fixture_path):
    raw_sexp = fixture_path.read_text()
    sexp = parse(raw_sexp)
    assert sexp
