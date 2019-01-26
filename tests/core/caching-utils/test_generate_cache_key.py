import enum

import pytest

from wasm._utils.caching import (
    generate_cache_key,
)


class SomeEnum(enum.Enum):
    a = 1
    b = 2
    c = 3


class SomeType:
    pass


@pytest.mark.parametrize(
    'value',
    (
        1,
        b'arst',
        'arst',
        (1, 2, 3),
        {'a': 1, 'b': 2, 'c': 3},
        {'a': (1, 2), 'b': (3, 4), 'c': 3},
        (SomeEnum.a, SomeEnum.b, 3),
        SomeType,
        (SomeType, 2, 3),
    )
)
def test_generate_cache_key(value):
    key_a = generate_cache_key(value)
    key_b = generate_cache_key(value)

    assert key_a == key_b


def test_generate_cache_key_with_internal_mutable_value():
    value = (1, 2, {'a': 1})

    key_a = generate_cache_key(value)

    # now mutate an inner value
    value[2]['a'] = 2

    key_b = generate_cache_key(value)

    assert key_a != key_b
