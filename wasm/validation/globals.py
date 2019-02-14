from wasm.datatypes import (
    Global,
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


def validate_global(context: Context, global_: Global) -> None:
    """
    Validate a Global object
    """
    expected_result_type = (global_.type.valtype,)

    with context.expression_context() as ctx:
        expression = Block.wrap((global_.type.valtype,), global_.init)
        validate_expression(expression, ctx)

    result_type = ctx.result_type

    if result_type != expected_result_type:
        raise ValidationError(
            f"Initialization code fro global variable result type does not "
            f"match global value type: {result_type} != {expected_result_type}"
        )

    with context.expression_context() as ctx:
        validate_constant_expression(global_.init, ctx)
