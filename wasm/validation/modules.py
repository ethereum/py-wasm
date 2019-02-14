from typing import (
    Iterable,
    Tuple,
    Union,
)

from wasm._utils.validation import (
    get_duplicates,
)
from wasm.datatypes import (
    FunctionIdx,
    FunctionType,
    GlobalIdx,
    GlobalType,
    MemoryIdx,
    MemoryType,
    Module,
    TableIdx,
    TableType,
    TypeIdx,
)
from wasm.exceptions import (
    ValidationError,
)

from .context import (
    Context,
)
from .data_segment import (
    validate_data_segment,
)
from .element_segment import (
    validate_element_segment,
)
from .exports import (
    validate_export,
)
from .function import (
    validate_function,
    validate_function_type,
    validate_start_function,
)
from .globals import (
    validate_global,
)
from .imports import (
    validate_import,
)
from .memory import (
    validate_memory,
)
from .tables import (
    validate_table,
)

TExtern = Union[FunctionType, TableType, MemoryType, GlobalType]


def get_import_function_types(imports: Iterable[TExtern]) -> Tuple[FunctionType, ...]:
    """
    Helper function for returning only the FunctionType elements from an
    iterable of Extern values.
    """
    return tuple(item for item in imports if isinstance(item, FunctionType))


def get_import_table_types(imports: Iterable[TExtern]) -> Tuple[TableType, ...]:
    """
    Helper function for returning only the TableType elements from an
    iterable of Extern values.
    """
    return tuple(item for item in imports if isinstance(item, TableType))


def get_import_memory_types(imports: Iterable[TExtern]) -> Tuple[MemoryType, ...]:
    """
    Helper function for returning only the MemoryType elements from an
    iterable of Extern values.
    """
    return tuple(item for item in imports if isinstance(item, MemoryType))


def get_import_global_types(imports: Iterable[TExtern]) -> Tuple[GlobalType, ...]:
    """
    Helper function for returning only the GlobalType elements from an
    iterable of Extern values.
    """
    return tuple(item for item in imports if isinstance(item, GlobalType))


TExportDesc = Union[FunctionIdx, GlobalIdx, MemoryIdx, TableIdx]


def get_export_type(context: Context, descriptor: TExportDesc) -> TExtern:
    """
    Helper function to validate the descriptor for an Export and return the
    associated type.
    """
    if isinstance(descriptor, FunctionIdx):
        return context.get_function(descriptor)
    elif isinstance(descriptor, TableIdx):
        return context.get_table(descriptor)
    elif isinstance(descriptor, MemoryIdx):
        return context.get_mem(descriptor)
    elif isinstance(descriptor, GlobalIdx):
        return context.get_global(descriptor)
    else:
        raise ValidationError(f"Unknown export descriptor type: {type(descriptor)}")


TImportDesc = Union[TypeIdx, GlobalType, MemoryType, TableType]


def get_import_type(module: Module, descriptor: TImportDesc) -> TExtern:
    """
    Helper function to validate the descriptor for an Import and return the
    associated extern type.
    """
    if isinstance(descriptor, TypeIdx):
        if descriptor >= len(module.types):
            raise ValidationError(
                f"Invalid import descriptor.  Type index is out of range. "
                f"type_idx={descriptor} > {len(module.types)}"
            )
        return module.types[descriptor]
    elif isinstance(descriptor, (TableType, MemoryType, GlobalType)):
        return descriptor
    else:
        raise ValidationError(f"Unknown import descriptor type: {type(descriptor)}")


def validate_function_types(module: Module) -> None:
    """
    Validate the function types for a module
    """
    # This validation is explicitly in the spec but it gives us strong
    # guarantees about indexing into the module types to populate the function
    # types.
    for function in module.funcs:
        if function.type_idx >= len(module.types):
            raise ValidationError(
                f"Function type index is out of range. "
                f"type_idx={function.type_idx} > {len(module.types)}"
            )


def validate_module(module: Module) -> Tuple[Tuple[TExtern, ...], Tuple[TExtern, ...]]:
    """
    Validatie a web Assembly module.
    """
    validate_function_types(module)

    module_function_types = tuple(
        module.types[function.type_idx]
        for function in module.funcs
    )

    module_table_types = tuple(table.type for table in module.tables)
    module_memory_types = tuple(mem.type for mem in module.mems)
    module_global_types = tuple(global_.type for global_ in module.globals)

    all_import_types = tuple(
        get_import_type(module, import_.desc)
        for import_ in module.imports
    )

    # let i_tstar be the concatenation of imports of each type
    import_function_types = get_import_function_types(all_import_types)
    import_table_types = get_import_table_types(all_import_types)
    import_memory_types = get_import_memory_types(all_import_types)
    import_global_types = get_import_global_types(all_import_types)

    context = Context(
        types=module.types,
        functions=import_function_types + module_function_types,
        tables=import_table_types + module_table_types,
        mems=import_memory_types + module_memory_types,
        globals=import_global_types + module_global_types,
        locals=(),
        labels=(),
        returns=(),

    )

    for functypei in module.types:
        validate_function_type(functypei)

    for function, function_type in zip(module.funcs, module_function_types):
        validate_function(context, function, function_type.results)

    for table in module.tables:
        validate_table(table)

    for memory in module.mems:
        validate_memory(memory)

    global_context = Context(
        types=(),
        functions=(),
        tables=(),
        mems=(),
        globals=tuple(import_global_types),
        locals=(),
        labels=(),
        returns=(),
    )
    for global_ in module.globals:
        validate_global(global_context, global_)

    for elem in module.elem:
        validate_element_segment(context, elem)

    for data in module.data:
        validate_data_segment(context, data)

    if module.start is not None:
        validate_start_function(context, module.start)

    for import_ in module.imports:
        validate_import(context, import_)

    for export in module.exports:
        validate_export(context, export)

    if len(context.tables) > 1:
        raise ValidationError(
            "Modules may have at most one table.  Found {len(context.tables)}"
        )
    elif len(context.mems) > 1:
        raise ValidationError(
            "Modules may have at most one memory.  Found {len(context.mems)}"
        )

    # export names must be unique
    duplicate_exports: Tuple[str, ...] = get_duplicates(export.name for export in module.exports)
    if duplicate_exports:
        raise ValidationError(
            "Duplicate module name(s) exported: "
            f"{'|'.join(sorted(duplicate_exports))}"
        )

    all_export_types = tuple(
        get_export_type(context, export.desc)
        for export in module.exports
    )

    # TODO: remove return value and decouple extraction of import/export types
    # from validation.
    return (all_import_types, all_export_types)
