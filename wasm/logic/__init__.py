from typing import (
    TYPE_CHECKING,
    Dict,
    Callable,
)

from wasm.opcodes import (
    BinaryOpcode,
)

from . import control
from . import memory
from . import numeric
from . import parametric
from . import variable

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
    BinaryOpcode.DROP: parametric.drop_op,
    BinaryOpcode.SELECT: parametric.select_op,
    BinaryOpcode.GET_LOCAL: variable.get_local_op,
    BinaryOpcode.SET_LOCAL: variable.set_local_op,
    BinaryOpcode.TEE_LOCAL: variable.tee_local_op,
    BinaryOpcode.GET_GLOBAL: variable.get_global_op,
    BinaryOpcode.SET_GLOBAL: variable.set_global_op,
    BinaryOpcode.I32_LOAD: memory.load_op,
    BinaryOpcode.I64_LOAD: memory.load_op,
    BinaryOpcode.F32_LOAD: memory.load_op,
    BinaryOpcode.F64_LOAD: memory.load_op,
    BinaryOpcode.I32_LOAD8_S: memory.load_op,
    BinaryOpcode.I32_LOAD8_U: memory.load_op,
    BinaryOpcode.I32_LOAD16_S: memory.load_op,
    BinaryOpcode.I32_LOAD16_U: memory.load_op,
    BinaryOpcode.I64_LOAD8_S: memory.load_op,
    BinaryOpcode.I64_LOAD8_U: memory.load_op,
    BinaryOpcode.I64_LOAD16_S: memory.load_op,
    BinaryOpcode.I64_LOAD16_U: memory.load_op,
    BinaryOpcode.I64_LOAD32_S: memory.load_op,
    BinaryOpcode.I64_LOAD32_U: memory.load_op,
    BinaryOpcode.I32_STORE: memory.store_op,
    BinaryOpcode.I64_STORE: memory.store_op,
    BinaryOpcode.F32_STORE: memory.store_op,
    BinaryOpcode.F64_STORE: memory.store_op,
    BinaryOpcode.I32_STORE8: memory.store_op,
    BinaryOpcode.I32_STORE16: memory.store_op,
    BinaryOpcode.I64_STORE8: memory.store_op,
    BinaryOpcode.I64_STORE16: memory.store_op,
    BinaryOpcode.I64_STORE32: memory.store_op,
    BinaryOpcode.MEMORY_SIZE: memory.memory_size_op,
    BinaryOpcode.MEMORY_GROW: memory.memory_grow_op,
    BinaryOpcode.I32_CONST: numeric.const_op,
    BinaryOpcode.I64_CONST: numeric.const_op,
    BinaryOpcode.F32_CONST: numeric.const_op,
    BinaryOpcode.F64_CONST: numeric.const_op,
    BinaryOpcode.I32_EQZ: numeric.ieqz_op,
    BinaryOpcode.I32_EQ: numeric.ieq_op,
    BinaryOpcode.I32_NE: numeric.ine_op,
    BinaryOpcode.I32_LT_S: numeric.i32lts_op,
    BinaryOpcode.I32_LT_U: numeric.iltu_op,
    BinaryOpcode.I32_GT_S: numeric.i32gts_op,
    BinaryOpcode.I32_GT_U: numeric.igtu_op,
    BinaryOpcode.I32_LE_S: numeric.i32les_op,
    BinaryOpcode.I32_LE_U: numeric.ileu_op,
    BinaryOpcode.I32_GE_S: numeric.i32ges_op,
    BinaryOpcode.I32_GE_U: numeric.igeu_op,
    BinaryOpcode.I64_EQZ: numeric.ieqz_op,
    BinaryOpcode.I64_EQ: numeric.ieq_op,
    BinaryOpcode.I64_NE: numeric.ine_op,
    BinaryOpcode.I64_LT_S: numeric.i64lts_op,
    BinaryOpcode.I64_LT_U: numeric.iltu_op,
    BinaryOpcode.I64_GT_S: numeric.i64gts_op,
    BinaryOpcode.I64_GT_U: numeric.igtu_op,
    BinaryOpcode.I64_LE_S: numeric.i64les_op,
    BinaryOpcode.I64_LE_U: numeric.ileu_op,
    BinaryOpcode.I64_GE_S: numeric.i64ges_op,
    BinaryOpcode.I64_GE_U: numeric.igeu_op,
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
    BinaryOpcode.I32_CLZ: numeric.i32clz_op,
    BinaryOpcode.I32_CTZ: numeric.i32ctz_op,
    BinaryOpcode.I32_POPCNT: numeric.ipopcnt_op,
    BinaryOpcode.I32_ADD: numeric.i32add_op,
    BinaryOpcode.I32_SUB: numeric.i32sub_op,
    BinaryOpcode.I32_MUL: numeric.i32mul_op,
    BinaryOpcode.I32_DIV_S: numeric.i32divs_op,
    BinaryOpcode.I32_DIV_U: numeric.idivu_op,
    BinaryOpcode.I32_REM_S: numeric.i32rems_op,
    BinaryOpcode.I32_REM_U: numeric.iremu_op,
    BinaryOpcode.I32_AND: numeric.iand_op,
    BinaryOpcode.I32_OR: numeric.ior_op,
    BinaryOpcode.I32_XOR: numeric.ixor_op,
    BinaryOpcode.I32_SHL: numeric.i32shl_op,
    BinaryOpcode.I32_SHR_S: numeric.i32shrs_op,
    BinaryOpcode.I32_SHR_U: numeric.i32shru_op,
    BinaryOpcode.I32_ROTL: numeric.i32rotl_op,
    BinaryOpcode.I32_ROTR: numeric.i32rotr_op,
    BinaryOpcode.I64_CLZ: numeric.i64clz_op,
    BinaryOpcode.I64_CTZ: numeric.i64ctz_op,
    BinaryOpcode.I64_POPCNT: numeric.ipopcnt_op,
    BinaryOpcode.I64_ADD: numeric.i64add_op,
    BinaryOpcode.I64_SUB: numeric.i64sub_op,
    BinaryOpcode.I64_MUL: numeric.i64mul_op,
    BinaryOpcode.I64_DIV_S: numeric.i64divs_op,
    BinaryOpcode.I64_DIV_U: numeric.idivu_op,
    BinaryOpcode.I64_REM_S: numeric.i64rems_op,
    BinaryOpcode.I64_REM_U: numeric.iremu_op,
    BinaryOpcode.I64_AND: numeric.iand_op,
    BinaryOpcode.I64_OR: numeric.ior_op,
    BinaryOpcode.I64_XOR: numeric.ixor_op,
    BinaryOpcode.I64_SHL: numeric.i64shl_op,
    BinaryOpcode.I64_SHR_S: numeric.i64shrs_op,
    BinaryOpcode.I64_SHR_U: numeric.i64shru_op,
    BinaryOpcode.I64_ROTL: numeric.i64rotl_op,
    BinaryOpcode.I64_ROTR: numeric.i64rotr_op,
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
