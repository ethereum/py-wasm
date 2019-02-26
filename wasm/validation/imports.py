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
    """
    Validate a Import object
    """
    validate_import_descriptor(context, import_.desc)


TImportDesc = Union[TypeIdx, GlobalType, MemoryType, TableType]


def validate_import_descriptor(context: Context, descriptor: TImportDesc) -> None:
    """
    Validate the descriptor component of an Import object
    """
    if type(descriptor) is TypeIdx:
        context.validate_type_idx(descriptor)
    elif type(descriptor) is TableType:
        validate_table_type(descriptor)
    elif type(descriptor) is MemoryType:
        validate_memory_type(descriptor)
    elif type(descriptor) is GlobalType:
        pass
    else:
        raise ValidationError(f"Unknown import descriptor type: {type(descriptor)}")
