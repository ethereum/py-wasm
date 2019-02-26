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
    module_name: str
    as_name: str
    desc: Union[TypeIdx, GlobalType, MemoryType, TableType]

    @property
    def type_idx(self) -> TypeIdx:
        if type(self.desc) is TypeIdx:
            return self.desc
        else:
            raise TypeError(f"Import descriptor of type: {type(self.desc)}")

    @property
    def is_function(self):
        return type(self.desc) is TypeIdx

    @property
    def is_global(self):
        return type(self.desc) is GlobalType

    @property
    def is_memory(self):
        return type(self.desc) is MemoryType

    @property
    def is_table(self):
        return type(self.desc) is TableType
