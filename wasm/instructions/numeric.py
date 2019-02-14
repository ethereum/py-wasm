import enum
from typing import (
    NamedTuple,
    Optional,
)

import numpy

from wasm._utils.interned import (
    Interned,
)
from wasm.datatypes import (
    ValType,
)
from wasm.opcodes import (
    BinaryOpcode,
)

from .base import (
    SimpleOp,
    register,
)


#
# Numeric
#
@register
class I32Const(NamedTuple):
    opcode: BinaryOpcode
    valtype: ValType
    value: numpy.uint32

    def __str__(self) -> str:
        return f"{self.opcode.text}[{self.value}]"

    @classmethod
    def from_opcode(cls,
                    opcode: BinaryOpcode,
                    value: numpy.uint32) -> 'I32Const':
        if opcode is not BinaryOpcode.I32_CONST:
            raise TypeError(f"Invalid opcode: {opcode}")
        return cls(opcode, ValType.i32, value)


@register
class I64Const(NamedTuple):
    opcode: BinaryOpcode
    valtype: ValType
    value: numpy.uint64

    def __str__(self) -> str:
        return f"{self.opcode.text}[{self.value}]"

    @classmethod
    def from_opcode(cls,
                    opcode: BinaryOpcode,
                    value: numpy.uint64) -> 'I64Const':
        if opcode is not BinaryOpcode.I64_CONST:
            raise TypeError(f"Invalid opcode: {opcode}")
        return cls(opcode, ValType.i64, value)


@register
class F32Const(NamedTuple):
    opcode: BinaryOpcode
    valtype: ValType
    value: numpy.float32

    def __str__(self) -> str:
        return f"{self.opcode.text}[{self.value}]"

    @classmethod
    def from_opcode(cls,
                    opcode: BinaryOpcode,
                    value: numpy.float32) -> 'F32Const':
        if opcode is not BinaryOpcode.F32_CONST:
            raise TypeError(f"Invalid opcode: {opcode}")
        return cls(opcode, ValType.f32, value)


@register
class F64Const(NamedTuple):
    opcode: BinaryOpcode
    valtype: ValType
    value: numpy.float64

    def __str__(self) -> str:
        return f"{self.opcode.text}[{self.value}]"

    @classmethod
    def from_opcode(cls,
                    opcode: BinaryOpcode,
                    value: numpy.float64) -> 'F64Const':
        if opcode is not BinaryOpcode.F64_CONST:
            raise TypeError(f"Invalid opcode: {opcode}")
        return cls(opcode, ValType.f64, value)


class Comparison(enum.Enum):
    eq = 'eq'
    ne = 'ne'
    lt = 'lt'
    gt = 'gt'
    le = 'le'
    ge = 'ge'
    lt_s = 'lt_s'
    lt_u = 'lt_u'
    gt_s = 'gt_s'
    gt_u = 'gt_u'
    le_s = 'le_s'
    le_u = 'le_u'
    ge_s = 'ge_s'
    ge_u = 'ge_u'

    @property
    def signed(self) -> Optional[bool]:
        if self is Comparison.eq:
            return None
        elif self is Comparison.ne:
            return None
        elif self in {Comparison.lt_s, Comparison.gt_s, Comparison.le_s, Comparison.ge_s}:
            return True
        elif self in {Comparison.lt_u, Comparison.gt_u, Comparison.le_u, Comparison.ge_u}:
            return False
        else:
            raise Exception("Invariant")


# TODO: All of the following numeric operation classes could be
# converted to a singleton pattern to reduce object churn.  This could also
# include the classes themselves handling extracting things like valtype or the
# comparison from the opcode itself rather than how it is currently done in the
# parser, resulting in stronger guarantees that these classes cannot be
# instantiated with invalid parameters.
@register
class RelOp(Interned):
    def __init__(self,
                 opcode: BinaryOpcode,
                 valtype: ValType,
                 comparison: Comparison) -> None:
        self.opcode = opcode
        self.valtype = valtype
        self.comparison = comparison

    def __str__(self) -> str:
        return self.opcode.text

    @classmethod
    def from_opcode(cls, opcode: BinaryOpcode) -> 'RelOp':
        # i32relop
        if opcode is BinaryOpcode.I32_EQ:
            return cls(opcode, ValType.i32, Comparison.eq)
        elif opcode is BinaryOpcode.I32_NE:
            return cls(opcode, ValType.i32, Comparison.ne)
        elif opcode is BinaryOpcode.I32_LT_S:
            return cls(opcode, ValType.i32, Comparison.lt_s)
        elif opcode is BinaryOpcode.I32_LT_U:
            return cls(opcode, ValType.i32, Comparison.lt_u)
        elif opcode is BinaryOpcode.I32_GT_S:
            return cls(opcode, ValType.i32, Comparison.gt_s)
        elif opcode is BinaryOpcode.I32_GT_U:
            return cls(opcode, ValType.i32, Comparison.gt_u)
        elif opcode is BinaryOpcode.I32_LE_S:
            return cls(opcode, ValType.i32, Comparison.le_s)
        elif opcode is BinaryOpcode.I32_LE_U:
            return cls(opcode, ValType.i32, Comparison.le_u)
        elif opcode is BinaryOpcode.I32_GE_S:
            return cls(opcode, ValType.i32, Comparison.ge_s)
        elif opcode is BinaryOpcode.I32_GE_U:
            return cls(opcode, ValType.i32, Comparison.ge_u)
        # i64relop
        elif opcode is BinaryOpcode.I64_EQ:
            return cls(opcode, ValType.i64, Comparison.eq)
        elif opcode is BinaryOpcode.I64_NE:
            return cls(opcode, ValType.i64, Comparison.ne)
        elif opcode is BinaryOpcode.I64_LT_S:
            return cls(opcode, ValType.i64, Comparison.lt_s)
        elif opcode is BinaryOpcode.I64_LT_U:
            return cls(opcode, ValType.i64, Comparison.lt_u)
        elif opcode is BinaryOpcode.I64_GT_S:
            return cls(opcode, ValType.i64, Comparison.gt_s)
        elif opcode is BinaryOpcode.I64_GT_U:
            return cls(opcode, ValType.i64, Comparison.gt_u)
        elif opcode is BinaryOpcode.I64_LE_S:
            return cls(opcode, ValType.i64, Comparison.le_s)
        elif opcode is BinaryOpcode.I64_LE_U:
            return cls(opcode, ValType.i64, Comparison.le_u)
        elif opcode is BinaryOpcode.I64_GE_S:
            return cls(opcode, ValType.i64, Comparison.ge_s)
        elif opcode is BinaryOpcode.I64_GE_U:
            return cls(opcode, ValType.i64, Comparison.ge_u)
        # f32relop
        elif opcode is BinaryOpcode.F32_EQ:
            return cls(opcode, ValType.f32, Comparison.eq)
        elif opcode is BinaryOpcode.F32_NE:
            return cls(opcode, ValType.f32, Comparison.ne)
        elif opcode is BinaryOpcode.F32_LT:
            return cls(opcode, ValType.f32, Comparison.lt)
        elif opcode is BinaryOpcode.F32_GT:
            return cls(opcode, ValType.f32, Comparison.gt)
        elif opcode is BinaryOpcode.F32_LE:
            return cls(opcode, ValType.f32, Comparison.le)
        elif opcode is BinaryOpcode.F32_GE:
            return cls(opcode, ValType.f32, Comparison.ge)
        # f64relop
        elif opcode is BinaryOpcode.F64_EQ:
            return cls(opcode, ValType.f64, Comparison.eq)
        elif opcode is BinaryOpcode.F64_NE:
            return cls(opcode, ValType.f64, Comparison.ne)
        elif opcode is BinaryOpcode.F64_LT:
            return cls(opcode, ValType.f64, Comparison.lt)
        elif opcode is BinaryOpcode.F64_GT:
            return cls(opcode, ValType.f64, Comparison.gt)
        elif opcode is BinaryOpcode.F64_LE:
            return cls(opcode, ValType.f64, Comparison.le)
        elif opcode is BinaryOpcode.F64_GE:
            return cls(opcode, ValType.f64, Comparison.ge)
        else:
            raise Exception(f"Invariant: got unknown opcode {opcode}")


@register
class UnOp(Interned):
    def __init__(self,
                 opcode: BinaryOpcode,
                 valtype: ValType) -> None:
        self.opcode = opcode
        self.valtype = valtype

    def __str__(self) -> str:
        return self.opcode.text

    @classmethod
    def from_opcode(cls, opcode: BinaryOpcode) -> 'UnOp':
        # i32
        if opcode is BinaryOpcode.I32_CLZ:
            return cls(opcode, ValType.i32)
        elif opcode is BinaryOpcode.I32_CTZ:
            return cls(opcode, ValType.i32)
        elif opcode is BinaryOpcode.I32_POPCNT:
            return cls(opcode, ValType.i32)
        # i64
        elif opcode is BinaryOpcode.I64_CLZ:
            return cls(opcode, ValType.i64)
        elif opcode is BinaryOpcode.I64_CTZ:
            return cls(opcode, ValType.i64)
        elif opcode is BinaryOpcode.I64_POPCNT:
            return cls(opcode, ValType.i64)
        # f32
        elif opcode is BinaryOpcode.F32_ABS:
            return cls(opcode, ValType.f32)
        elif opcode is BinaryOpcode.F32_NEG:
            return cls(opcode, ValType.f32)
        elif opcode is BinaryOpcode.F32_CEIL:
            return cls(opcode, ValType.f32)
        elif opcode is BinaryOpcode.F32_FLOOR:
            return cls(opcode, ValType.f32)
        elif opcode is BinaryOpcode.F32_TRUNC:
            return cls(opcode, ValType.f32)
        elif opcode is BinaryOpcode.F32_NEAREST:
            return cls(opcode, ValType.f32)
        elif opcode is BinaryOpcode.F32_SQRT:
            return cls(opcode, ValType.f32)
        # f64
        elif opcode is BinaryOpcode.F64_ABS:
            return cls(opcode, ValType.f64)
        elif opcode is BinaryOpcode.F64_NEG:
            return cls(opcode, ValType.f64)
        elif opcode is BinaryOpcode.F64_CEIL:
            return cls(opcode, ValType.f64)
        elif opcode is BinaryOpcode.F64_FLOOR:
            return cls(opcode, ValType.f64)
        elif opcode is BinaryOpcode.F64_TRUNC:
            return cls(opcode, ValType.f64)
        elif opcode is BinaryOpcode.F64_NEAREST:
            return cls(opcode, ValType.f64)
        elif opcode is BinaryOpcode.F64_SQRT:
            return cls(opcode, ValType.f64)
        else:
            raise Exception(f"Invariant: got unknown opcode {opcode}")


@register
class BinOp(Interned):
    def __init__(self,
                 opcode: BinaryOpcode,
                 valtype: ValType,
                 signed: Optional[bool]) -> None:
        self.opcode = opcode
        self.valtype = valtype
        self.signed = signed

    def __str__(self) -> str:
        return self.opcode.text

    @classmethod
    def from_opcode(cls, opcode: BinaryOpcode) -> 'BinOp':
        # i32
        if opcode is BinaryOpcode.I32_ADD:
            return cls(opcode, ValType.i32, None)
        elif opcode is BinaryOpcode.I32_SUB:
            return cls(opcode, ValType.i32, None)
        elif opcode is BinaryOpcode.I32_MUL:
            return cls(opcode, ValType.i32, None)
        elif opcode is BinaryOpcode.I32_DIV_S:
            return cls(opcode, ValType.i32, True)
        elif opcode is BinaryOpcode.I32_DIV_U:
            return cls(opcode, ValType.i32, False)
        elif opcode is BinaryOpcode.I32_REM_S:
            return cls(opcode, ValType.i32, True)
        elif opcode is BinaryOpcode.I32_REM_U:
            return cls(opcode, ValType.i32, False)
        elif opcode is BinaryOpcode.I32_AND:
            return cls(opcode, ValType.i32, None)
        elif opcode is BinaryOpcode.I32_OR:
            return cls(opcode, ValType.i32, None)
        elif opcode is BinaryOpcode.I32_XOR:
            return cls(opcode, ValType.i32, None)
        elif opcode is BinaryOpcode.I32_SHL:
            return cls(opcode, ValType.i32, None)
        elif opcode is BinaryOpcode.I32_SHR_S:
            return cls(opcode, ValType.i32, True)
        elif opcode is BinaryOpcode.I32_SHR_U:
            return cls(opcode, ValType.i32, False)
        elif opcode is BinaryOpcode.I32_ROTL:
            return cls(opcode, ValType.i32, None)
        elif opcode is BinaryOpcode.I32_ROTR:
            return cls(opcode, ValType.i32, None)
        # i64
        elif opcode is BinaryOpcode.I64_ADD:
            return cls(opcode, ValType.i64, None)
        elif opcode is BinaryOpcode.I64_SUB:
            return cls(opcode, ValType.i64, None)
        elif opcode is BinaryOpcode.I64_MUL:
            return cls(opcode, ValType.i64, None)
        elif opcode is BinaryOpcode.I64_DIV_S:
            return cls(opcode, ValType.i64, True)
        elif opcode is BinaryOpcode.I64_DIV_U:
            return cls(opcode, ValType.i64, False)
        elif opcode is BinaryOpcode.I64_REM_S:
            return cls(opcode, ValType.i64, True)
        elif opcode is BinaryOpcode.I64_REM_U:
            return cls(opcode, ValType.i64, False)
        elif opcode is BinaryOpcode.I64_AND:
            return cls(opcode, ValType.i64, None)
        elif opcode is BinaryOpcode.I64_OR:
            return cls(opcode, ValType.i64, None)
        elif opcode is BinaryOpcode.I64_XOR:
            return cls(opcode, ValType.i64, None)
        elif opcode is BinaryOpcode.I64_SHL:
            return cls(opcode, ValType.i64, None)
        elif opcode is BinaryOpcode.I64_SHR_S:
            return cls(opcode, ValType.i64, True)
        elif opcode is BinaryOpcode.I64_SHR_U:
            return cls(opcode, ValType.i64, False)
        elif opcode is BinaryOpcode.I64_ROTL:
            return cls(opcode, ValType.i64, None)
        elif opcode is BinaryOpcode.I64_ROTR:
            return cls(opcode, ValType.i64, None)
        # f32
        elif opcode is BinaryOpcode.F32_ADD:
            return cls(opcode, ValType.f32, None)
        elif opcode is BinaryOpcode.F32_SUB:
            return cls(opcode, ValType.f32, None)
        elif opcode is BinaryOpcode.F32_MUL:
            return cls(opcode, ValType.f32, None)
        elif opcode is BinaryOpcode.F32_DIV:
            return cls(opcode, ValType.f32, None)
        elif opcode is BinaryOpcode.F32_MIN:
            return cls(opcode, ValType.f32, None)
        elif opcode is BinaryOpcode.F32_MAX:
            return cls(opcode, ValType.f32, None)
        elif opcode is BinaryOpcode.F32_COPYSIGN:
            return cls(opcode, ValType.f32, None)
        # f64
        elif opcode is BinaryOpcode.F64_ADD:
            return cls(opcode, ValType.f64, None)
        elif opcode is BinaryOpcode.F64_SUB:
            return cls(opcode, ValType.f64, None)
        elif opcode is BinaryOpcode.F64_MUL:
            return cls(opcode, ValType.f64, None)
        elif opcode is BinaryOpcode.F64_DIV:
            return cls(opcode, ValType.f64, None)
        elif opcode is BinaryOpcode.F64_MIN:
            return cls(opcode, ValType.f64, None)
        elif opcode is BinaryOpcode.F64_MAX:
            return cls(opcode, ValType.f64, None)
        elif opcode is BinaryOpcode.F64_COPYSIGN:
            return cls(opcode, ValType.f64, None)
        else:
            raise Exception(f"Invariant: got unknown opcode {opcode}")


@register
class TestOp(Interned):
    def __init__(self, opcode: BinaryOpcode, valtype: ValType) -> None:
        self.opcode = opcode
        self.valtype = valtype

    def __str__(self) -> str:
        return self.opcode.text

    @classmethod
    def from_opcode(cls, opcode: BinaryOpcode) -> 'TestOp':
        if opcode is BinaryOpcode.I32_EQZ:
            return cls(opcode, ValType.i32)
        elif opcode is BinaryOpcode.I64_EQZ:
            return cls(opcode, ValType.i64)
        else:
            raise Exception(f"Invariant: got unknown opcode {opcode}")


@register
class Wrap(SimpleOp):
    opcode = BinaryOpcode.I32_WRAP_I64
    valtype = ValType.i32
    from_valtype = ValType.i64


@register
class Truncate(Interned):
    def __init__(self,
                 opcode: BinaryOpcode,
                 valtype: ValType,
                 from_valtype: ValType,
                 signed: bool) -> None:
        self.opcode = opcode
        self.valtype = valtype
        self.from_valtype = from_valtype
        self.signed = signed

    def __str__(self) -> str:
        return self.opcode.text

    @classmethod
    def from_opcode(cls, opcode: BinaryOpcode) -> 'Truncate':
        if opcode is BinaryOpcode.I32_TRUNC_S_F32:
            return cls(opcode, ValType.i32, ValType.f32, True)
        elif opcode is BinaryOpcode.I32_TRUNC_U_F32:
            return cls(opcode, ValType.i32, ValType.f32, False)
        elif opcode is BinaryOpcode.I32_TRUNC_S_F64:
            return cls(opcode, ValType.i32, ValType.f64, True)
        elif opcode is BinaryOpcode.I32_TRUNC_U_F64:
            return cls(opcode, ValType.i32, ValType.f64, False)
        elif opcode is BinaryOpcode.I64_TRUNC_S_F32:
            return cls(opcode, ValType.i64, ValType.f32, True)
        elif opcode is BinaryOpcode.I64_TRUNC_U_F32:
            return cls(opcode, ValType.i64, ValType.f32, False)
        elif opcode is BinaryOpcode.I64_TRUNC_S_F64:
            return cls(opcode, ValType.i64, ValType.f64, True)
        elif opcode is BinaryOpcode.I64_TRUNC_U_F64:
            return cls(opcode, ValType.i64, ValType.f64, False)
        else:
            raise Exception(f"Invariant: got unknown opcode {opcode}")


@register
class Extend(Interned):
    def __init__(self,
                 opcode: BinaryOpcode,
                 valtype: ValType,
                 from_valtype: ValType,
                 signed: bool) -> None:
        self.opcode = opcode
        self.valtype = valtype
        self.from_valtype = from_valtype
        self.signed = signed

    def __str__(self) -> str:
        return self.opcode.text

    @classmethod
    def from_opcode(cls, opcode: BinaryOpcode) -> 'Extend':
        if opcode is BinaryOpcode.I64_EXTEND_S_I32:
            return cls(opcode, ValType.i64, ValType.i32, True)
        elif opcode is BinaryOpcode.I64_EXTEND_U_I32:
            return cls(opcode, ValType.i64, ValType.i32, False)
        else:
            raise Exception(f"Invariant: got unknown opcode {opcode}")


@register
class Demote(SimpleOp):
    opcode = BinaryOpcode.F32_DEMOTE_F64
    valtype = ValType.f32
    from_valtype = ValType.f64


@register
class Promote(SimpleOp):
    opcode = BinaryOpcode.F64_PROMOTE_F32
    valtype = ValType.f64
    from_valtype = ValType.f32


@register
class Convert(Interned):
    def __init__(self,
                 opcode: BinaryOpcode,
                 valtype: ValType,
                 from_valtype: ValType,
                 signed: bool) -> None:
        self.opcode = opcode
        self.valtype = valtype
        self.from_valtype = from_valtype
        self.signed = signed

    def __str__(self) -> str:
        return self.opcode.text

    @classmethod
    def from_opcode(cls, opcode: BinaryOpcode) -> 'Convert':
        if opcode is BinaryOpcode.F32_CONVERT_S_I32:
            return cls(opcode, ValType.f32, ValType.i32, True)
        elif opcode is BinaryOpcode.F32_CONVERT_U_I32:
            return cls(opcode, ValType.f32, ValType.i32, False)
        elif opcode is BinaryOpcode.F32_CONVERT_S_I64:
            return cls(opcode, ValType.f32, ValType.i64, True)
        elif opcode is BinaryOpcode.F32_CONVERT_U_I64:
            return cls(opcode, ValType.f32, ValType.i64, False)
        elif opcode is BinaryOpcode.F64_CONVERT_S_I32:
            return cls(opcode, ValType.f64, ValType.i32, True)
        elif opcode is BinaryOpcode.F64_CONVERT_U_I32:
            return cls(opcode, ValType.f64, ValType.i32, False)
        elif opcode is BinaryOpcode.F64_CONVERT_S_I64:
            return cls(opcode, ValType.f64, ValType.i64, True)
        elif opcode is BinaryOpcode.F64_CONVERT_U_I64:
            return cls(opcode, ValType.f64, ValType.i64, False)
        else:
            raise Exception(f"Invariant: got unknown opcode {opcode}")


@register
class Reinterpret(Interned):
    def __init__(self,
                 opcode: BinaryOpcode,
                 valtype: ValType,
                 from_valtype: ValType) -> None:
        self.opcode = opcode
        self.valtype = valtype
        self.from_valtype = from_valtype

    def __str__(self) -> str:
        return self.opcode.text

    @classmethod
    def from_opcode(cls, opcode: BinaryOpcode) -> 'Reinterpret':
        if opcode is BinaryOpcode.I32_REINTERPRET_F32:
            return cls(opcode, ValType.i32, ValType.f32)
        elif opcode is BinaryOpcode.I64_REINTERPRET_F64:
            return cls(opcode, ValType.i64, ValType.f64)
        elif opcode is BinaryOpcode.F32_REINTERPRET_I32:
            return cls(opcode, ValType.f32, ValType.i32)
        elif opcode is BinaryOpcode.F64_REINTERPRET_I64:
            return cls(opcode, ValType.f64, ValType.i64)
        else:
            raise Exception(f"Invariant: got unknown opcode {opcode}")
