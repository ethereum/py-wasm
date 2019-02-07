from typing import (
    TYPE_CHECKING,
    Dict,
    Callable,
)

from wasm.opcodes import (
    BinaryOpcode,
)

from . import control

if TYPE_CHECKING:
    from wasm.execution import (  # noqa:
        Configuration,
    )


OPCODE_TO_LOGIC_FN: Dict[BinaryOpcode, Callable[['Configuration'], None]] = {
    BinaryOpcode.UNREACHABLE: control.unreachable_op,
    BinaryOpcode.NOP: control.nop_op,
    BinaryOpcode.BLOCK: control.block_op,
    BinaryOpcode.LOOP: control.loop_op,
    BinaryOpcode.IF: control.if_op,
    BinaryOpcode.ELSE: control.else_op,
    BinaryOpcode.END: control.end_op,
    BinaryOpcode.BR: control.br_op,
    BinaryOpcode.BR_IF: control.br_if_op,
    BinaryOpcode.BR_TABLE: control.br_table_op,
    BinaryOpcode.RETURN: control.return_op,
    BinaryOpcode.CALL: control.call_op,
    BinaryOpcode.CALL_INDIRECT: control.call_indirect_op,
    BinaryOpcode.DROP: control.drop_op,
    BinaryOpcode.SELECT: control.select_op,
    # BinaryOpcode.GET_LOCAL:
    # BinaryOpcode.SET_LOCAL:
    # BinaryOpcode.TEE_LOCAL:
    # BinaryOpcode.GET_GLOBAL:
    # BinaryOpcode.SET_GLOBAL:
    # BinaryOpcode.I32_LOAD:
    # BinaryOpcode.I64_LOAD:
    # BinaryOpcode.F32_LOAD:
    # BinaryOpcode.F64_LOAD:
    # BinaryOpcode.I32_LOAD8_S:
    # BinaryOpcode.I32_LOAD8_U:
    # BinaryOpcode.I32_LOAD16_S:
    # BinaryOpcode.I32_LOAD16_U:
    # BinaryOpcode.I64_LOAD8_S:
    # BinaryOpcode.I64_LOAD8_U:
    # BinaryOpcode.I64_LOAD16_S:
    # BinaryOpcode.I64_LOAD16_U:
    # BinaryOpcode.I64_LOAD32_S:
    # BinaryOpcode.I64_LOAD32_U:
    # BinaryOpcode.I32_STORE:
    # BinaryOpcode.I64_STORE:
    # BinaryOpcode.F32_STORE:
    # BinaryOpcode.F64_STORE:
    # BinaryOpcode.I32_STORE8:
    # BinaryOpcode.I32_STORE16:
    # BinaryOpcode.I64_STORE8:
    # BinaryOpcode.I64_STORE16:
    # BinaryOpcode.I64_STORE32:
    # BinaryOpcode.MEMORY_SIZE:
    # BinaryOpcode.MEMORY_GROW:
    # BinaryOpcode.I32_CONST:
    # BinaryOpcode.I64_CONST:
    # BinaryOpcode.F32_CONST:
    # BinaryOpcode.F64_CONST:
    # BinaryOpcode.I32_EQZ:
    # BinaryOpcode.I32_EQ:
    # BinaryOpcode.I32_NE:
    # BinaryOpcode.I32_LT_S:
    # BinaryOpcode.I32_LT_U:
    # BinaryOpcode.I32_GT_S:
    # BinaryOpcode.I32_GT_U:
    # BinaryOpcode.I32_LE_S:
    # BinaryOpcode.I32_LE_U:
    # BinaryOpcode.I32_GE_S:
    # BinaryOpcode.I32_GE_U:
    # BinaryOpcode.I64_EQZ:
    # BinaryOpcode.I64_EQ:
    # BinaryOpcode.I64_NE:
    # BinaryOpcode.I64_LT_S:
    # BinaryOpcode.I64_LT_U:
    # BinaryOpcode.I64_GT_S:
    # BinaryOpcode.I64_GT_U:
    # BinaryOpcode.I64_LE_S:
    # BinaryOpcode.I64_LE_U:
    # BinaryOpcode.I64_GE_S:
    # BinaryOpcode.I64_GE_U:
    # BinaryOpcode.F32_EQ:
    # BinaryOpcode.F32_NE:
    # BinaryOpcode.F32_LT:
    # BinaryOpcode.F32_GT:
    # BinaryOpcode.F32_LE:
    # BinaryOpcode.F32_GE:
    # BinaryOpcode.F64_EQ:
    # BinaryOpcode.F64_NE:
    # BinaryOpcode.F64_LT:
    # BinaryOpcode.F64_GT:
    # BinaryOpcode.F64_LE:
    # BinaryOpcode.F64_GE:
    # BinaryOpcode.I32_CLZ:
    # BinaryOpcode.I32_CTZ:
    # BinaryOpcode.I32_POPCNT:
    # BinaryOpcode.I32_ADD:
    # BinaryOpcode.I32_SUB:
    # BinaryOpcode.I32_MUL:
    # BinaryOpcode.I32_DIV_S:
    # BinaryOpcode.I32_DIV_U:
    # BinaryOpcode.I32_REM_S:
    # BinaryOpcode.I32_REM_U:
    # BinaryOpcode.I32_AND:
    # BinaryOpcode.I32_OR:
    # BinaryOpcode.I32_XOR:
    # BinaryOpcode.I32_SHL:
    # BinaryOpcode.I32_SHR_S:
    # BinaryOpcode.I32_SHR_U:
    # BinaryOpcode.I32_ROTL:
    # BinaryOpcode.I32_ROTR:
    # BinaryOpcode.I64_CLZ:
    # BinaryOpcode.I64_CTZ:
    # BinaryOpcode.I64_POPCNT:
    # BinaryOpcode.I64_ADD:
    # BinaryOpcode.I64_SUB:
    # BinaryOpcode.I64_MUL:
    # BinaryOpcode.I64_DIV_S:
    # BinaryOpcode.I64_DIV_U:
    # BinaryOpcode.I64_REM_S:
    # BinaryOpcode.I64_REM_U:
    # BinaryOpcode.I64_AND:
    # BinaryOpcode.I64_OR:
    # BinaryOpcode.I64_XOR:
    # BinaryOpcode.I64_SHL:
    # BinaryOpcode.I64_SHR_S:
    # BinaryOpcode.I64_SHR_U:
    # BinaryOpcode.I64_ROTL:
    # BinaryOpcode.I64_ROTR:
    # BinaryOpcode.F32_ABS:
    # BinaryOpcode.F32_NEG:
    # BinaryOpcode.F32_CEIL:
    # BinaryOpcode.F32_FLOOR:
    # BinaryOpcode.F32_TRUNC:
    # BinaryOpcode.F32_NEAREST:
    # BinaryOpcode.F32_SQRT:
    # BinaryOpcode.F32_ADD:
    # BinaryOpcode.F32_SUB:
    # BinaryOpcode.F32_MUL:
    # BinaryOpcode.F32_DIV:
    # BinaryOpcode.F32_MIN:
    # BinaryOpcode.F32_MAX:
    # BinaryOpcode.F32_COPYSIGN:
    # BinaryOpcode.F64_ABS:
    # BinaryOpcode.F64_NEG:
    # BinaryOpcode.F64_CEIL:
    # BinaryOpcode.F64_FLOOR:
    # BinaryOpcode.F64_TRUNC:
    # BinaryOpcode.F64_NEAREST:
    # BinaryOpcode.F64_SQRT:
    # BinaryOpcode.F64_ADD:
    # BinaryOpcode.F64_SUB:
    # BinaryOpcode.F64_MUL:
    # BinaryOpcode.F64_DIV:
    # BinaryOpcode.F64_MIN:
    # BinaryOpcode.F64_MAX:
    # BinaryOpcode.F64_COPYSIGN:
    # BinaryOpcode.I32_WRAP_I64:
    # BinaryOpcode.I32_TRUNC_S_F32:
    # BinaryOpcode.I32_TRUNC_U_F32:
    # BinaryOpcode.I32_TRUNC_S_F64:
    # BinaryOpcode.I32_TRUNC_U_F64:
    # BinaryOpcode.I64_EXTEND_S_I32:
    # BinaryOpcode.I64_EXTEND_U_I32:
    # BinaryOpcode.I64_TRUNC_S_F32:
    # BinaryOpcode.I64_TRUNC_U_F32:
    # BinaryOpcode.I64_TRUNC_S_F64:
    # BinaryOpcode.I64_TRUNC_U_F64:
    # BinaryOpcode.F32_CONVERT_S_I32:
    # BinaryOpcode.F32_CONVERT_U_I32:
    # BinaryOpcode.F32_CONVERT_S_I64:
    # BinaryOpcode.F32_CONVERT_U_I64:
    # BinaryOpcode.F32_DEMOTE_F64:
    # BinaryOpcode.F64_CONVERT_S_I32:
    # BinaryOpcode.F64_CONVERT_U_I32:
    # BinaryOpcode.F64_CONVERT_S_I64:
    # BinaryOpcode.F64_CONVERT_U_I64:
    # BinaryOpcode.F64_PROMOTE_F32:
    # BinaryOpcode.I32_REINTERPRET_F32:
    # BinaryOpcode.I64_REINTERPRET_F64:
    # BinaryOpcode.F32_REINTERPRET_I32:
    # BinaryOpcode.F64_REINTERPRET_I64:
    # # special case
    # InvokeOp:
}
