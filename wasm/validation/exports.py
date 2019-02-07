from typing import (
    Union,
)

from wasm.datatypes import (
    Export,
    FunctionIdx,
    FunctionType,
    GlobalIdx,
    GlobalType,
    MemoryIdx,
    MemoryType,
    TableIdx,
    TableType,
)
from wasm.exceptions import (
    ValidationError,
)

from .context import (
    Context,
)

TExportValue = Union[FunctionType, TableType, MemoryType, GlobalType]
TExportDesc = Union[FunctionIdx, GlobalIdx, MemoryIdx, TableIdx]


def validate_export(context: Context, export: Export) -> TExportValue:
    return validate_export_descriptor(context, export.desc)


def validate_export_descriptor(context: Context,
                               descriptor: TExportDesc) -> TExportValue:
    if isinstance(descriptor, FunctionIdx):
        context.validate_function_idx(descriptor)
        return context.get_function(descriptor)
    elif isinstance(descriptor, TableIdx):
        context.validate_table_idx(descriptor)
        return context.get_table(descriptor)
    elif isinstance(descriptor, MemoryIdx):
        context.validate_mem_idx(descriptor)
        return context.get_mem(descriptor)
    elif isinstance(descriptor, GlobalIdx):
        context.validate_global_idx(descriptor)
        return context.get_global(descriptor)
    else:
        raise ValidationError(f"Unknown export descriptor type: {type(descriptor)}")
