from typing import (
    Tuple,
    cast,
)

from wasm.datatypes import (
    Function,
    FunctionType,
    ValType,
)
from wasm.exceptions import (
    ValidationError,
)
from wasm.instructions import (
    BaseInstruction,
    Block,
)

from .context import (
    Context,
)
from .expressions import (
    validate_expression,
)


def validate_function_type(function_type: FunctionType) -> None:
    if len(function_type.results) > 1:
        raise ValidationError(
            f"Function types may only have one result.  Got {len(function_type.results)}"
        )


def validate_function(context: Context,
                      function: Function,
                      expected_result_type: Tuple[ValType, ...]) -> None:
    context.validate_type_idx(function.type_idx)
    function_type = context.get_type(function.type_idx)

    ctx = context.expression_context(
        locals=tuple(function_type.params + function.locals),
        labels=function_type.results,
        returns=function_type.results,
    )
    with ctx:
        # validate body using algorithm in appendix
        instrstar = cast(Tuple[BaseInstruction, ...], (
            Block(
                function_type.results,
                function.body,
            ),
        ))
        validate_expression(instrstar, ctx)

    result_type = ctx.result_type
    if result_type != expected_result_type:
        raise ValidationError(
            f"Function result type does not match declared result type: "
            f"{result_type} != {expected_result_type}"
        )
