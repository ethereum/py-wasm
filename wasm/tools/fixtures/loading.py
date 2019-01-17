from pathlib import (
    Path,
)
from typing import (
    Tuple,
)


def find_json_fixture_files(fixtures_base_dir: Path) -> Tuple[Path, ...]:
    all_fixture_paths = tuple(fixtures_base_dir.glob('**/*.json'))
    return all_fixture_paths
