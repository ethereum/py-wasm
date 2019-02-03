from wasm.datatypes import (
    ElementSegment,
    FunctionAddress,
    ValType,
)
from wasm.exceptions import (
    ValidationError,
)
from wasm.instructions import (
    Block,
)

from .context import (
    Context,
)
from .expressions import (
    validate_constant_expression,
    validate_expression,
)


def validate_element_segment(context: Context, element_segment: ElementSegment) -> None:
    context.validate_table_idx(element_segment.table_idx)
    table_type = context.get_table(element_segment.table_idx)

    elem_type = table_type.elem_type
    if elem_type is not FunctionAddress:
        raise ValidationError(
            f"Table has invalid element type.  Expected `FunctionAddress`. "
            f"Got: `{elem_type}`"
        )

    expected_result_type = (ValType.i32,)
    with context.expression_context() as ctx:
        expression = Block.wrap(expected_result_type, element_segment.offset)
        validate_expression(expression, ctx)

    result_type = ctx.result_type

    if result_type != expected_result_type:
        raise ValidationError(
            f"Invalid data segment.  Return type must be '(i32,)'.  Got "
            f"{result_type}"
        )

    with context.expression_context() as ctx:
        validate_constant_expression(element_segment.offset, ctx)

    for function_idx in element_segment.init:
        context.validate_function_idx(function_idx)
