from typing import (
    NamedTuple,
    Union,
)

from .indices import (
    FuncIdx,
    GlobalIdx,
    MemoryIdx,
    TableIdx,
)


class Export(NamedTuple):
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#memory-types%E2%91%A0
    """
    name: str
    desc: Union[FuncIdx, GlobalIdx, MemoryIdx, TableIdx]

    @property
    def is_function(self):
        return isinstance(self.desc, FuncIdx)

    @property
    def func_idx(self) -> FuncIdx:
        if isinstance(self.desc, FuncIdx):
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
