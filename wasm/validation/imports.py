from typing import (
    Union,
)

from wasm.datatypes import (
    FunctionType,
    GlobalType,
    Import,
    MemoryType,
    TableType,
    TypeIdx,
)
from wasm.exceptions import (
    ValidationError,
)

from .context import (
    Context,
)
from .memory import (
    validate_memory_type,
)
from .tables import (
    validate_table_type,
)

TImport = Union[FunctionType, TableType, MemoryType, GlobalType]


def validate_import(context: Context, import_: Import) -> None:
    validate_import_descriptor(context, import_.desc)


TImportDesc = Union[TypeIdx, GlobalType, MemoryType, TableType]


def validate_import_descriptor(context: Context, descriptor: TImportDesc) -> None:
    if isinstance(descriptor, TypeIdx):
        context.validate_type_idx(descriptor)
    elif isinstance(descriptor, TableType):
        validate_table_type(descriptor)
    elif isinstance(descriptor, MemoryType):
        validate_memory_type(descriptor)
    elif isinstance(descriptor, GlobalType):
        pass
    else:
        raise ValidationError(f"Unknown import descriptor type: {type(descriptor)}")
