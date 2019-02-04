from typing import (
    Union,
)

from wasm.datatypes import (
    FunctionType,
    GlobalType,
    Limits,
    MemoryType,
    TableType,
)
from wasm.exceptions import (
    ValidationError,
)

TLimits = Union[Limits, MemoryType]


def validate_limits_match(limits_a: TLimits, limits_b: TLimits) -> None:
    if limits_a.min < limits_b.min:
        raise ValidationError(f"Limits.min mismatch: {limits_a.min} != {limits_b.min}")
    elif limits_b.max is None:
        return
    elif limits_a.max is not None and limits_a.max <= limits_b.max:
        return
    else:
        raise ValidationError(f"Limits.max mismatch: {limits_a.max} != {limits_b.max}")


def validate_external_type_match(external_type_a, external_type_b):
    if type(external_type_a) is not type(external_type_b):
        raise ValidationError(
            f"Mismatch in extern types: {type(external_type_a)} != "
            f"{type(external_type_b)}"
        )
    elif isinstance(external_type_a, FunctionType):
        if external_type_a != external_type_b:
            raise ValidationError(
                f"Function types not equal: {external_type_a} != {external_type_b}"
            )
    elif isinstance(external_type_a, TableType):
        validate_limits_match(external_type_a.limits, external_type_b.limits)

        if external_type_a.elem_type is not external_type_b.elem_type:
            raise ValidationError(
                f"Table element type mismatch: {external_type_a.elem_type} != "
                f"{external_type_b.elem_type}"
            )
    elif isinstance(external_type_a, MemoryType):
        validate_limits_match(external_type_a, external_type_b)
    elif isinstance(external_type_a, GlobalType):
        if external_type_a != external_type_b:
            raise ValidationError(
                f"Globals extern type mismatch: {external_type_a} != {external_type_b}"
            )
    else:
        raise Exception(f"Invariant: unknown extern type: {type(external_type_a)}")
