from typing import (
    NamedTuple,
    Union,
    cast,
)

from .addresses import (
    FunctionAddress,
    GlobalAddress,
    MemoryAddress,
    TableAddress,
)
from .indices import (
    FunctionIdx,
    GlobalIdx,
    MemoryIdx,
    TableIdx,
)


class Export(NamedTuple):
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#memory-types%E2%91%A0
    """
    name: str
    desc: Union[FunctionIdx, GlobalIdx, MemoryIdx, TableIdx]

    @property
    def is_function(self):
        return type(self.desc) is FunctionIdx

    @property
    def function_idx(self) -> FunctionIdx:
        if type(self.desc) is FunctionIdx:
            return self.desc
        else:
            raise TypeError(f"Export descriptor of type: {type(self.desc)}")

    @property
    def is_global(self):
        return type(self.desc) is GlobalIdx

    @property
    def global_idx(self) -> GlobalIdx:
        if type(self.desc) is GlobalIdx:
            return self.desc
        else:
            raise TypeError(f"Export descriptor of type: {type(self.desc)}")

    @property
    def is_memory(self):
        return type(self.desc) is MemoryIdx

    @property
    def memory_idx(self) -> MemoryIdx:
        if type(self.desc) is MemoryIdx:
            return self.desc
        else:
            raise TypeError(f"Export descriptor of type: {type(self.desc)}")

    @property
    def is_table(self):
        return type(self.desc) is TableIdx

    @property
    def table_idx(self) -> TableIdx:
        if type(self.desc) is TableIdx:
            return self.desc
        else:
            raise TypeError(f"Export descriptor of type: {type(self.desc)}")


class ExportInstance(NamedTuple):
    name: str
    value: Union[FunctionAddress, TableAddress, MemoryAddress, GlobalAddress]

    @property
    def is_function(self):
        return type(self.value) is FunctionAddress

    @property
    def function_address(self) -> FunctionAddress:
        return cast(FunctionAddress, self.value)
