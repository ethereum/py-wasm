from typing import (
    NamedTuple,
)

from wasm.typing import (
    ExportDesc,
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
    desc: ExportDesc

    @property
    def is_function(self):
        return isinstance(self.desc, FuncIdx)

    @property
    def is_global(self):
        return isinstance(self.desc, GlobalIdx)

    @property
    def is_memory(self):
        return isinstance(self.desc, MemoryIdx)

    @property
    def is_table(self):
        return isinstance(self.desc, TableIdx)
