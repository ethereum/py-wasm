from typing import (
    Any,
    Dict,
    Type,
)


class Singleton:
    _cache: Dict[Type['Singleton'], 'Singleton'] = {}

    def __new__(cls, *args: Any, **kwargs: Any) -> 'Singleton':
        if cls not in cls._cache:
            instance = super().__new__(cls)
            if args or kwargs:
                raise TypeError("Singleton does not allow arguments")
            cls._cache[cls] = instance
        return cls._cache[cls]
