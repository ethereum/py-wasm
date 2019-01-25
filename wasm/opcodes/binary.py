import enum


class BinaryOpcode(enum.Enum):
    #
    # Control: 5.4.1
    #
    UNREACHABLE = 0x00  # unreachable
    NOP = 0x01  # nop
    BLOCK = 0x02  # block  # blocktype in* end		# begin block
    LOOP = 0x03  # loop  # blocktype in* end		# begin block
    IF = 0x04  # if  # blocktype in1* else? end	# begin block
    ELSE = 0x05  # else  # in2*				# end block & begin block
    END = 0x0B  # end  # end block
    BR = 0x0C  # br  # labelidx			# branch
    BR_IF = 0x0D  # br_if  # labelidx			# branch
    BR_TABLE = 0x0E  # br_table  # labelidx* labelidx		# branch
    RETURN = 0x0F  # return  # end outermost block
    CALL = 0x10  # call  # funcidx			# branch
    CALL_INDIRECT = 0x11  # call_indirect  # typeidx 0x00			# branch

    @property
    def is_control(self):
        return 0x00 <= self.value <= 0x11

    #
    # Parametric: 5.4.2
    #
    DROP = 0x1A  # drop
    SELECT = 0x1B  # select

    @property
    def is_parametric(self) -> bool:
        return self is self.DROP or self is self.SELECT

    #
    # Variable: 5.4.3
    #
    GET_LOCAL = 0x20  # get_local  # localidx
    SET_LOCAL = 0x21  # set_local  # localidx
    TEE_LOCAL = 0x22  # tee_local  # localidx
    GET_GLOBAL = 0x23  # get_global  # globalidx
    SET_GLOBAL = 0x24  # set_global  # globalidx

    @property
    def is_variable(self) -> bool:
        return 0x20 <= self.value <= 0x24

    #
    # Memory: 5.4.5
    #
    I32_LOAD = 0x28  # i32.load  # memarg
    I64_LOAD = 0x29  # i64.load  # memarg
    F32_LOAD = 0x2A  # f32.load  # memarg
    F64_LOAD = 0x2B  # f64.load  # memarg
    I32_LOAD8_S = 0x2C  # i32.load8_s  # memarg
    I32_LOAD8_U = 0x2D  # i32.load8_u  # memarg
    I32_LOAD16_S = 0x2E  # i32.load16_s  # memarg
    I32_LOAD16_U = 0x2F  # i32.load16_u  # memarg
    I64_LOAD8_S = 0x30  # i64.load8_s  # memarg
    I64_LOAD8_U = 0x31  # i64.load8_u  # memarg
    I64_LOAD16_S = 0x32  # i64.load16_s  # memarg
    I64_LOAD16_U = 0x33  # i64.load16_u  # memarg
    I64_LOAD32_S = 0x34  # i64.load32_s  # memarg
    I64_LOAD32_U = 0x35  # i64.load32_u  # memarg
    I32_STORE = 0x36  # i32.store  # memarg
    I64_STORE = 0x37  # i64.store  # memarg
    F32_STORE = 0x38  # f32.store  # memarg
    F64_STORE = 0x39  # f64.store  # memarg
    I32_STORE8 = 0x3A  # i32.store8  # memarg
    I32_STORE16 = 0x3B  # i32.store16  # memarg
    I64_STORE8 = 0x3C  # i64.store8  # memarg
    I64_STORE16 = 0x3D  # i64.store16  # memarg
    I64_STORE32 = 0x3E  # i64.store32  # memarg
    MEMORY_SIZE = 0x3F  # memory.size
    MEMORY_GROW = 0x40  # memory.grow

    @property
    def is_memory(self) -> bool:
        return 0x28 <= self.value <= 0x40

    @property
    def is_memory_load(self) -> bool:
        return 0x28 <= self.value <= 0x35

    @property
    def is_memory_store(self) -> bool:
        return 0x36 <= self.value <= 0x3e

    @property
    def is_memory_access(self) -> bool:
        return self.is_memory_load or self.is_memory_store

    @property
    def is_memory_size_change(self) -> bool:
        return 0x3f <= self.value <= 0x40

    #
    # Numeric: 5.4.5
    #
    I32_CONST = 0x41  # i32.const  # i32
    I64_CONST = 0x42  # i64.const  # i64
    F32_CONST = 0x43  # f32.const  # f32
    F64_CONST = 0x44  # f64.const  # f64

    @property
    def is_numeric_constant(self) -> bool:
        return 0x41 <= self.value <= 0x44

    # i32testop
    I32_EQZ = 0x45  # i32.eqz

    # i32relop
    I32_EQ = 0x46  # i32.eq
    I32_NE = 0x47  # i32.ne
    I32_LT_S = 0x48  # i32.lt_s
    I32_LT_U = 0x49  # i32.lt_u
    I32_GT_S = 0x4A  # i32.gt_s
    I32_GT_U = 0x4B  # i32.gt_u
    I32_LE_S = 0x4C  # i32.le_s
    I32_LE_U = 0x4D  # i32.le_u
    I32_GE_S = 0x4E  # i32.ge_s
    I32_GE_U = 0x4F  # i32.ge_u

    # i64testop
    I64_EQZ = 0x50  # i64.eqz

    @property
    def is_testop(self):
        return self is self.I32_EQZ or self is self.I64_EQZ

    # i64relop
    I64_EQ = 0x51  # i64.eq
    I64_NE = 0x52  # i64.ne
    I64_LT_S = 0x53  # i64.lt_s
    I64_LT_U = 0x54  # i64.lt_u
    I64_GT_S = 0x55  # i64.gt_s
    I64_GT_U = 0x56  # i64.gt_u
    I64_LE_S = 0x57  # i64.le_s
    I64_LE_U = 0x58  # i64.le_u
    I64_GE_S = 0x59  # i64.ge_s
    I64_GE_U = 0x5A  # i64.ge_u

    # frelop
    F32_EQ = 0x5B  # f32.eq
    F32_NE = 0x5C  # f32.ne
    F32_LT = 0x5D  # f32.lt
    F32_GT = 0x5E  # f32.gt
    F32_LE = 0x5F  # f32.le
    F32_GE = 0x60  # f32.ge
    F64_EQ = 0x61  # f64.eq
    F64_NE = 0x62  # f64.ne
    F64_LT = 0x63  # f64.lt
    F64_GT = 0x64  # f64.gt
    F64_LE = 0x65  # f64.le
    F64_GE = 0x66  # f64.ge

    @property
    def is_relop(self) -> bool:
        if 0x46 <= self.value <= 0x4f:
            return True  # i32
        elif 0x51 <= self.value <= 0x66:
            return True  # i64/f32/f64
        else:
            return False

    # i32unop
    I32_CLZ = 0x67  # i32.clz
    I32_CTZ = 0x68  # i32.ctz
    I32_POPCNT = 0x69  # i32.popcnt

    # i32binop
    I32_ADD = 0x6A  # i32.add
    I32_SUB = 0x6B  # i32.sub
    I32_MUL = 0x6C  # i32.mul
    I32_DIV_S = 0x6D  # i32.div_s
    I32_DIV_U = 0x6E  # i32.div_u
    I32_REM_S = 0x6F  # i32.rem_s
    I32_REM_U = 0x70  # i32.rem_u
    I32_AND = 0x71  # i32.and
    I32_OR = 0x72  # i32.or
    I32_XOR = 0x73  # i32.xor
    I32_SHL = 0x74  # i32.shl
    I32_SHR_S = 0x75  # i32.shr_s
    I32_SHR_U = 0x76  # i32.shr_u
    I32_ROTL = 0x77  # i32.rotl
    I32_ROTR = 0x78  # i32.rotr

    # i64unop
    I64_CLZ = 0x79  # i64.clz
    I64_CTZ = 0x7A  # i64.ctz
    I64_POPCNT = 0x7B  # i64.popcnt

    # i64binop
    I64_ADD = 0x7C  # i64.add
    I64_SUB = 0x7D  # i64.sub
    I64_MUL = 0x7E  # i64.mul
    I64_DIV_S = 0x7F  # i64.div_s
    I64_DIV_U = 0x80  # i64.div_u
    I64_REM_S = 0x81  # i64.rem_s
    I64_REM_U = 0x82  # i64.rem_u
    I64_AND = 0x83  # i64.and
    I64_OR = 0x84  # i64.or
    I64_XOR = 0x85  # i64.xor
    I64_SHL = 0x86  # i64.shl
    I64_SHR_S = 0x87  # i64.shr_s
    I64_SHR_U = 0x88  # i64.shr_u
    I64_ROTL = 0x89  # i64.rotl
    I64_ROTR = 0x8A  # i64.rotr

    # f32unop
    F32_ABS = 0x8B  # f32.abs
    F32_NEG = 0x8C  # f32.neg
    F32_CEIL = 0x8D  # f32.ceil
    F32_FLOOR = 0x8E  # f32.floor
    F32_TRUNC = 0x8F  # f32.trunc
    F32_NEAREST = 0x90  # f32.nearest
    F32_SQRT = 0x91  # f32.sqrt

    # f32binop
    F32_ADD = 0x92  # f32.add
    F32_SUB = 0x93  # f32.sub
    F32_MUL = 0x94  # f32.mul
    F32_DIV = 0x95  # f32.div
    F32_MIN = 0x96  # f32.min
    F32_MAX = 0x97  # f32.max
    F32_COPYSIGN = 0x98  # f32.copysign

    # f64unop
    F64_ABS = 0x99  # f64.abs
    F64_NEG = 0x9A  # f64.neg
    F64_CEIL = 0x9B  # f64.ceil
    F64_FLOOR = 0x9C  # f64.floor
    F64_TRUNC = 0x9D  # f64.trunc
    F64_NEAREST = 0x9E  # f64.nearest
    F64_SQRT = 0x9F  # f64.sqrt

    # f64binop
    F64_ADD = 0xA0  # f64.add
    F64_SUB = 0xA1  # f64.sub
    F64_MUL = 0xA2  # f64.mul
    F64_DIV = 0xA3  # f64.div
    F64_MIN = 0xA4  # f64.min
    F64_MAX = 0xA5  # f64.max
    F64_COPYSIGN = 0xA6  # f64.copysign

    # converstions
    I32_WRAP_I64 = 0xA7  # i32.wrap/i64
    I32_TRUNC_S_F32 = 0xA8  # i32.trunc_s/f32
    I32_TRUNC_U_F32 = 0xA9  # i32.trunc_u/f32
    I32_TRUNC_S_F64 = 0xAA  # i32.trunc_s/f64
    I32_TRUNC_U_F64 = 0xAB  # i32.trunc_u/f64
    I64_EXTEND_S_I32 = 0xAC  # i64.extend_s/i32
    I64_EXTEND_U_I32 = 0xAD  # i64.extend_u/i32
    I64_TRUNC_S_F32 = 0xAE  # i64.trunc_s/f32
    I64_TRUNC_U_F32 = 0xAF  # i64.trunc_u/f32
    I64_TRUNC_S_F64 = 0xB0  # i64.trunc_s/f64
    I64_TRUNC_U_F64 = 0xB1  # i64.trunc_u/f64
    F32_CONVERT_S_I32 = 0xB2  # f32.convert_s/i32
    F32_CONVERT_U_I32 = 0xB3  # f32.convert_u/i32
    F32_CONVERT_S_I64 = 0xB4  # f32.convert_s/i64
    F32_CONVERT_U_I64 = 0xB5  # f32.convert_u/i64
    F32_DEMOTE_F64 = 0xB6  # f32.demote/f64
    F64_CONVERT_S_I32 = 0xB7  # f64.convert_s/i32
    F64_CONVERT_U_I32 = 0xB8  # f64.convert_u/i32
    F64_CONVERT_S_I64 = 0xB9  # f64.convert_s/i64
    F64_CONVERT_U_I64 = 0xBA  # f64.convert_u/i64
    F64_PROMOTE_F32 = 0xBB  # f64.promote/f32
    I32_REINTERPRET_F32 = 0xBC  # i32.reinterpret/f32
    I64_REINTERPRET_F64 = 0xBD  # i64.reinterpret/f64
    F32_REINTERPRET_I32 = 0xBE  # f32.reinterpret/i32
    F64_REINTERPRET_I64 = 0xBF  # f64.reinterpret/i64

    @property
    def is_numeric(self) -> bool:
        return 0x41 <= self.value <= 0xbf

    @property
    def is_unop(self) -> bool:
        if 0x67 <= self.value <= 0x69:
            return True  # i32
        elif 0x79 <= self.value <= 0x7b:
            return True  # i64
        elif 0x8b <= self.value <= 0x91:
            return True  # f32
        elif 0x99 <= self.value <= 0x9f:
            return True  # f64
        else:
            return False

    @property
    def is_binop(self) -> bool:
        if 0x6a <= self.value <= 0x78:
            return True
        elif 0x7c <= self.value <= 0x8a:
            return True
        elif 0x92 <= self.value <= 0x98:
            return True
        elif 0xa0 <= self.value <= 0xa6:
            return True
        else:
            return False

    @property
    def is_conversion(self) -> bool:
        return 0xa7 <= self.value <= 0xbf

    @property
    def is_truncate(self) -> bool:
        if 0xa8 <= self.value <= 0xab:
            return True
        elif 0xae <= self.value <= 0xb1:
            return True
        else:
            return False

    @property
    def is_convert(self) -> bool:
        if 0xb2 <= self.value <= 0xb5:
            return True
        elif 0xb7 <= self.value <= 0xba:
            return True
        else:
            return False

    @property
    def is_reinterpret(self) -> bool:
        return 0xbc <= self.value <= 0xbf

    @property
    def text(self) -> str:
        from .text import OPCODE_TO_TEXT
        return OPCODE_TO_TEXT[self]
