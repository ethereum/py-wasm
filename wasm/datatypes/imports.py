from typing import (
    NamedTuple,
    Union,
)

from .globals import (
    GlobalType,
)
from .indices import (
    TypeIdx,
)
from .memory import (
    MemoryType,
)
from .table import (
    TableType,
)


class Import(NamedTuple):
    module: str
    name: str
    desc: Union[TypeIdx, GlobalType, MemoryType, TableType]

    @property
    def type_idx(self) -> TypeIdx:
        if isinstance(self.desc, TypeIdx):
            return self.desc
        else:
            raise TypeError(f"Import descriptor of type: {type(self.desc)}")

    @property
    def is_function(self):
        return isinstance(self.desc, TypeIdx)

    @property
    def is_global(self):
        return isinstance(self.desc, GlobalType)

    @property
    def is_memory(self):
        return isinstance(self.desc, MemoryType)

    @property
    def is_table(self):
        return isinstance(self.desc, TableType)
