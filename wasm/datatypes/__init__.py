from .addresses import (  # noqa: F401
    FunctionAddress,
    GlobalAddress,
    MemoryAddress,
    TableAddress,
)
from .bit_size import (  # noqa: F401
    BitSize,
)
from .code import (  # noqa: F401
    Code,
    LocalsMeta,
)
from .data_segment import (  # noqa: F401
    DataSegment,
)
from .element_segment import (  # noqa: F401
    ElementSegment,
)
from .exports import (  # noqa: F401
    Export,
    ExportInstance,
)
from .function import (  # noqa: F401
    BaseFunctionInstance,
    Function,
    FunctionType,
    HostFunction,
    StartFunction,
)
from .globals import (  # noqa: F401
    Global,
    GlobalInstance,
    GlobalType,
)
from .imports import (  # noqa: F401
    Import,
)
from .indices import (  # noqa: F401
    FunctionIdx,
    GlobalIdx,
    LabelIdx,
    LocalIdx,
    MemoryIdx,
    TableIdx,
    TypeIdx,
)
from .limits import (  # noqa: F401
    Limits,
)
from .memory import (  # noqa: F401
    Memory,
    MemoryInstance,
    MemoryType,
)
from .module import (  # noqa: F401
    FunctionInstance,
    Module,
    ModuleInstance,
)
from .mutability import (  # noqa: F401
    Mutability,
)
from .sections import (  # noqa: F401
    CodeSection,
    CustomSection,
    DataSegmentSection,
    ElementSegmentSection,
    ExportSection,
    FunctionSection,
    GlobalSection,
    ImportSection,
    MemorySection,
    StartSection,
    TableSection,
    TypeSection,
)
from .store import (  # noqa: F401
    Store,
)
from .table import (  # noqa: F401
    Table,
    TableInstance,
    TableType,
)
from .valtype import (  # noqa: F401
    ValType,
)

BaseFunctionInstance.register(FunctionInstance)
