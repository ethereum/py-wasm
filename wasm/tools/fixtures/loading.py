import fnmatch
import os
from pathlib import (
    Path,
)
from typing import (
    Iterable,
)

from eth_utils import (
    to_tuple,
)


@to_tuple
def recursive_find_files(base_dir: Path, pattern: str) -> Iterable[Path]:
    for dirpath, _, filenames in os.walk(str(base_dir)):
        for filename in filenames:
            if fnmatch.fnmatch(filename, pattern):
                yield Path(os.path.join(dirpath, filename))


def find_json_fixture_files(fixtures_base_dir: Path) -> Iterable[Path]:
    all_fixture_paths = recursive_find_files(fixtures_base_dir, "*.json")
    return all_fixture_paths
