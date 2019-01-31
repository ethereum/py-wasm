from .addresses import (  # noqa: F401
    FunctionAddress,
    GlobalAddress,
    MemoryAddress,
    TableAddress,
)
from .bit_size import (  # noqa: F401
    BitSize,
)
from .configuration import (  # noqa: F401
    Configuration,
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
    FuncIdx,
    GlobalIdx,
    LabelIdx,
    LocalIdx,
    MemoryIdx,
    TableIdx,
    TypeIdx,
)
from .instructions import (  # noqa: F401
    InstructionSequence,
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
from .stack import (  # noqa: F401
    Frame,
    FrameStack,
    Label,
    LabelStack,
    ValueStack,
)
from .table import (  # noqa: F401
    Table,
    TableInstance,
    TableType,
)
from .val_type import (  # noqa: F401
    ValType,
)


BaseFunctionInstance.register(FunctionInstance)
