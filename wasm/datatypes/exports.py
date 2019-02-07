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
        return isinstance(self.desc, FunctionIdx)

    @property
    def function_idx(self) -> FunctionIdx:
        if isinstance(self.desc, FunctionIdx):
            return self.desc
        else:
            raise TypeError(f"Export descriptor of type: {type(self.desc)}")

    @property
    def is_global(self):
        return isinstance(self.desc, GlobalIdx)

    @property
    def global_idx(self) -> GlobalIdx:
        if isinstance(self.desc, GlobalIdx):
            return self.desc
        else:
            raise TypeError(f"Export descriptor of type: {type(self.desc)}")

    @property
    def is_memory(self):
        return isinstance(self.desc, MemoryIdx)

    @property
    def memory_idx(self) -> MemoryIdx:
        if isinstance(self.desc, MemoryIdx):
            return self.desc
        else:
            raise TypeError(f"Export descriptor of type: {type(self.desc)}")

    @property
    def is_table(self):
        return isinstance(self.desc, TableIdx)

    @property
    def table_idx(self) -> TableIdx:
        if isinstance(self.desc, TableIdx):
            return self.desc
        else:
            raise TypeError(f"Export descriptor of type: {type(self.desc)}")


class ExportInstance(NamedTuple):
    name: str
    value: Union[FunctionAddress, TableAddress, MemoryAddress, GlobalAddress]

    @property
    def is_function(self):
        return isinstance(self.value, FunctionAddress)

    @property
    def function_address(self) -> FunctionAddress:
        return cast(FunctionAddress, self.value)

    @property
    def is_global(self):
        return isinstance(self.value, GlobalAddress)

    @property
    def global_address(self) -> GlobalAddress:
        return cast(GlobalAddress, self.value)

    @property
    def is_memory(self):
        return isinstance(self.value, MemoryAddress)

    @property
    def memory_address(self) -> MemoryAddress:
        return cast(MemoryAddress, self.value)

    @property
    def is_table(self):
        return isinstance(self.value, TableAddress)

    @property
    def table_address(self) -> TableAddress:
        return cast(TableAddress, self.value)
