from collections.abc import (
    Hashable,
    Mapping,
    Sequence,
)
from typing import (
    Union,
)

Cachable = Union[
    Hashable,
    'Mapping[Hashable, Hashable]',
    'Sequence[Hashable]',
]


def generate_cache_key(value: Cachable) -> int:
    """
    Generates a cache key for the *args and **kwargs
    """
    if isinstance(value, Sequence):
        if isinstance(value, (bytes, str)):
            return hash(value)
        else:
            return hash(tuple(
                generate_cache_key(item)
                for item in value
            ))
    elif isinstance(value, Mapping):
        return hash(tuple(
            generate_cache_key((key, value[key]))
            for key in sorted(value.keys())
        ))
    elif isinstance(value, Hashable):
        return hash(value)
    else:
        raise TypeError(
            f"Cannot generate cache key for value {value} of type "
            f"{type(value)}"
        )
