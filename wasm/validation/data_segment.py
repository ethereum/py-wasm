from wasm.datatypes import (
    DataSegment,
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


def validate_data_segment(context: Context, data_segment: DataSegment) -> None:
    context.validate_mem_idx(data_segment.memory_idx)

    expected_result_type = (ValType.i32,)
    with context.expression_context() as ctx:
        expression = Block.wrap(expected_result_type, data_segment.offset)
        validate_expression(expression, ctx)

    result_type = ctx.result_type

    if result_type != expected_result_type:
        raise ValidationError(
            f"Invalid data segment.  Return type must be '(i32,)'.  Got "
            f"{result_type}"
        )

    with context.expression_context() as ctx:
        validate_constant_expression(data_segment.offset, ctx)
