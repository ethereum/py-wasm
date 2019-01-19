import pytest

from wasm._utils.validation import (
    get_duplicates,
)


@pytest.mark.parametrize(
    'seq,expected',
    (
        (tuple(), tuple()),
        ((1,), tuple()),
        ((1, 2), tuple()),
        ((1, 2, 1), (1,)),
        ((1, 1, 2), (1,)),
        ((1, 1, 2, 3, 4, 3), (1, 3)),
        # iterator
        ((v for v in (1, 1, 2, 3, 4, 3)), (1, 3)),
    ),
)
def test_get_duplicates(seq, expected):
    actual = get_duplicates(seq)
    assert actual == expected
