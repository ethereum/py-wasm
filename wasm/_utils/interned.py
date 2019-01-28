from typing import (
    Any,
    Dict,
    Tuple,
)
from weakref import (
    WeakValueDictionary,
)

from .caching import (
    generate_cache_key,
)


class Interned:
    """
    Base class for immutable data types such that any two instantiations with
    the same constructor arguments will return the same object
    """
    _cache: "WeakValueDictionary[int, 'Interned']" = WeakValueDictionary()

    def __new__(cls, *args: Tuple[Any, ...], **kwargs: Dict[Any, Any]) -> 'Interned':
        cache_key = generate_cache_key((cls, args, kwargs))
        if cache_key not in cls._cache:
            instance = super().__new__(cls)
            instance.__init__(*args, **kwargs)
            cls._cache[cache_key] = instance
        return cls._cache[cache_key]
