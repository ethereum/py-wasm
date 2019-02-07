from typing import IO

from wasm.datatypes import (
    Function,
    Module,
)
from wasm.exceptions import (
    MalformedModule,
)

from .magic import (
    parse_magic,
)
from .sections import (
    parse_sections,
)
from .version import (
    parse_version,
)


def parse_module(stream: IO[bytes]) -> Module:
    # `parse_magic` both parses and validates the 4-byte *magic* preamble.
    # Curretly we simply discard this value.
    parse_magic(stream)
    version = parse_version(stream)

    (
        custom_sections,
        type_section,
        import_section,
        function_section,
        table_section,
        memory_section,
        global_section,
        export_section,
        start_section,
        element_segment_section,
        code_section,
        data_segment_section,
    ) = parse_sections(stream)

    if len(function_section.types) != len(code_section.codes):
        raise MalformedModule(
            "Mismatched lengths of function section and code section. "
            f"function-types[{len(function_section.types)}] != "
            f"codes[{len(code_section.codes)}]"
        )

    functions = tuple(
        Function(type_idx, code.locals, code.expr)
        for type_idx, code
        in zip(function_section.types, code_section.codes)
    )

    module = Module(
        version=version,
        types=type_section.function_types,
        funcs=functions,
        tables=table_section.tables,
        mems=memory_section.mems,
        globals=global_section.globals,
        elem=element_segment_section.element_segments,
        data=data_segment_section.data_segments,
        start=start_section.start,
        imports=import_section.imports,
        exports=export_section.exports,
    )
    return module
