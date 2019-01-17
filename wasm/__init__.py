#!/usr/bin/env python3

"""
University of Illinois/NCSA Open Source License
Copyright (c) 2018 Paul Dworzanski
All rights reserved.

Developed by: 		Paul Dworzanski
                        Ethereum Foundation
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal with the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimers.
Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimers in the documentation and/or other materials provided with the distribution.
Neither the names of Paul Dworzanski, Ethereum Foundation, nor the names of its contributors may be used to endorse or promote products derived from this Software without specific prior written permission.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS WITH THE SOFTWARE.
"""


"""
This code follows the WebAssembly spec closely. Differences from spec follow.
 - We drop types and just hold values eg instead of `i32.const 5`, we just hold value `5`. This is done for locals, globals, and the value stack. The only place types remain are arguments when using the API to invoke an exported function, which is useful for type-checking, but we may choose to relax this in favor of checking whether each value meets requirements for its type.
- Floating-point operations use the Python `float`, which are 64-bit on modern computers. We truncate to 32-bit when necessary. We use the `math` module for floating-point tools and the `struct` module to encode/decode binary. The `NaN` is difficult to modify in Python, so we completely ignore `NaN`'s significand, unlike the spec. We are considering re-implementing floating-point operations using:
   - ctypes.c_float and ctypes.c_double, but these may have less features
   - numpy.float32 and numpy.float64, but these are less portable
   - the decimal module, tuned to behave like IEEE754-2008
 - Unlike the spec, we modify the `store` in-place. Make a deep-copy if needed.
 - Exection in the spec uses rewrite/substitution rules on the instruction sequence, but this would be inefficient, so, like most implementations, we maintain stacks instead of modifying the instruction sequence. This is explained more in section 4.4.5 below.
 - In instantiate_module() we also return the return value, since there seems to be no other way to get the value returned by the start function. We will approach the spec writers about this.
"""
import logging
import math  # for some floating-point methods
import struct  # for encoding/decoding floats
from typing import NamedTuple

from wasm import (
    constants,
)
from wasm.exceptions import (
    Exhaustion,
    InvalidModule,
    MalformedModule,
    Trap,
    Unlinkable,
    ValidationError,
)
from wasm._utils.types import (
    get_bit_size,
    get_float_type,
    is_float_type,
    is_integer_type,
)


logger = logging.getLogger('wasm.spec')


###############
###############
# 2 STRUCTURE #
###############
###############

# Chapter 2 defines the abstract syntax, which is used throughout the implementation. Not much is needed from this section, since most abstrct syntax is nested lists and dictionaries

# 2.2.3 FLOATING-POINT

# functions in this sectio are not currently used since we decided to use native Python floats, and struct.pack()/unpack() to encode/decode, but we may use these later to pass the rest of the NaN tests


def spec_fN(N, f):
    fNmag = spec_fNmag(N, f)
    if f >= 0:
        return fNmag
    else:
        return -1 * fNmag


def spec_fNmag(N, f):
    # TODO: this function appears to be a noop
    M = spec_signif(N)
    E = spec_expon(N)
    e = bitstring[1 : E + 1]
    m = bitstring[E + 1 :]
    if -1 * (2 ** (E - 1)) + 2 <= e <= 2 ** (E - 1) - 1:
        pass


def spec_signif(N):
    logging.debug("spec_signif(%s)", N)

    if N == 32:
        return 23
    elif N == 64:
        return 52
    else:
        raise Exception(f"Invariant: got '{N}' | expected one of 32/64")


def spec_signif_inv(signif):
    logging.debug("spec_signif_inv(%s)", N)

    if signif == 23:
        return 32
    elif signif == 52:
        return 64
    else:
        raise Exception(f"Invariant: got '{N}' | expected one of 32/64")


def spec_expon(N):
    logging.debug("spec_expon(%s)", N)

    if N == 32:
        return 8
    elif N == 64:
        return 11
    else:
        raise Exception(f"Invariant: got '{N}' | expected one of 32/64")


def spec_expon_inv(expon):
    logging.debug("spec_expon_inv(%s)", expon)

    if expon == 8:
        return 32
    elif expon == 11:
        return 64
    else:
        raise Exception(f"Invariant: got '{expon}' | expected one of 8/11")


# 2.3.8 EXTERNAL TYPES

# similar things are defined in 2.5.10 and 4.2.11, we will reuse these for those


def spec_funcs(star):
    funcs = []
    for e in star:
        if e[0] == "func":
            funcs += [e[1]]
    return funcs


def spec_tables(star):
    tables = []
    for e in star:
        if e[0] == "table":
            tables += [e[1]]
    return tables


def spec_mems(star):
    mems = []
    for e in star:
        if e[0] == "mem":
            mems += [e[1]]
    return mems


def spec_globals(star):
    globals_ = []
    for e in star:
        if e[0] == "global":
            globals_ += [e[1]]
    return globals_


################
################
# 3 VALIDATION #
################
################

# Chapter 3 defines validation rules over the abstract syntax. These rules constrain the syntax, but provide properties such as type-safety. An almost-complete implementation is available as a feature-branch.


###########
# 3.2 TYPES
###########

# 3.2.1 LIMITS


def spec_validate_limit(limits, k):
    n = limits["min"]
    m = limits["max"]
    if n > k:
        raise InvalidModule("invalid")
    if m != None and (m > k or m < n):
        raise InvalidModule("invalid")
    return k


# 3.2.2 FUNCTION TYPES


def spec_validate_functype(ft):
    if len(ft[1]) > 1:
        raise InvalidModule("invalid")
    return ft


# 3.2.3 TABLE TYPES


def spec_validate_tabletype(tt):
    limits, elemtype = tt
    # TODO: use of UINT32_CEIL may be incorrect here as `validate_limit` checks
    # against the value using `>`.  Check looks like it **should** be using
    # `>=` to ensure that the limit bounds fit withint a UINT32 but updating
    # this to use `UINT32_MAX` is currently causing spec test failures.
    spec_validate_limit(limits, constants.UINT32_CEIL)
    return tt


# 3.2.4 MEMORY TYPES


def spec_validate_memtype(limits):
    # TODO: use of UINT32_CEIL may be incorrect here as `validate_limit` checks
    # against the value using `>`.  Check looks like it **should** be using
    # `>=` to ensure that the limit bounds fit withint a UINT32 but updating
    # this to use `UINT32_MAX` is currently causing spec test failures.
    spec_validate_limit(limits, constants.UINT16_CEIL)
    return limits


# 3.2.5 GLOBAL TYPES


def spec_validate_globaltype(globaltype):
    return (
        globaltype
    )  # TODO: always valid, maybe should check whether mut and valtype are both ok


##################
# 3.3 INSTRUCTIONS
##################

# 3.3.1 NUMERIC INSTRUCTIONS


def spec_validate_t_const(t):
    return [], [t]


def spec_validate_t_unop(t):
    return [t], [t]


def spec_validate_t_binop(t):
    return [t, t], [t]


def spec_validate_t_testop(t):
    return [t], [constants.INT32]


def spec_validate_t_relop(t):
    return [t, t], [constants.INT32]


def spec_validate_t2_cvtop_t1(t1, t2):
    return [t1], [t2]


# 3.3.2  PARAMETRIC INSTRUCTIONS


def spec_validate_drop():
    return ["t"], []


def spec_validate_select():
    return ["t", "t", constants.INT32], ["t"]


# 3.3.3 VARIABLE INSTRUCTIONS


def spec_validate_get_local(C, x):
    if len(C["locals"]) <= x:
        raise InvalidModule("invalid")
    t = C["locals"][x]
    return [], [t]


def spec_validate_set_local(C, x):
    if len(C["locals"]) <= x:
        raise InvalidModule("invalid")
    t = C["locals"][x]
    return [t], []


def spec_validate_tee_local(C, x):
    if len(C["locals"]) <= x:
        raise InvalidModule("invalid")
    t = C["locals"][x]
    return [t], [t]


def spec_validate_get_global(C, x):
    if len(C["globals"]) <= x:
        raise InvalidModule("invalid")
    mut, t = C.globals[x]
    return [], [t]


def spec_validate_set_global(C, x):
    if len(C["globals"]) <= x:
        raise InvalidModule("invalid")
    mut, t = C.globals[x]
    if mut != "var":
        raise InvalidModule("invalid")
    return [t], []


# 3.3.4 MEMORY INSTRUCTIONS


def spec_validate_t_load(C, t, memarg):
    if len(C["mems"]) < 1:
        raise InvalidModule("invalid")
    tval = get_bit_size(t)  # invariant: t has form: letter digit digit  eg i32
    if 2 ** memarg["align"] > tval // 8:
        raise InvalidModule("invalid")
    return [constants.INT32], [t]


def spec_validate_tloadNsx(C, t, N, memarg):
    if len(C["mems"]) < 1:
        raise InvalidModule("invalid")
    if 2 ** memarg["align"] > N // 8:
        raise InvalidModule("invalid")
    return [constants.INT32], [t]


def spec_validate_tstore(C, t, memarg):
    if len(C["mems"]) < 1:
        raise InvalidModule("invalid")
    tval = get_bit_size(t)  # invariant: t has form: letter digit digit  eg i32
    if 2 ** memarg["align"] > tval // 8:
        raise InvalidModule("invalid")
    return [constants.INT32, t], []


def spec_validate_tstoreN(C, t, N, memarg):
    if len(C["mems"]) < 1:
        raise InvalidModule("invalid")
    if 2 ** memarg["align"] > N // 8:
        raise InvalidModule("invalid")
    return [constants.INT32, t], []


def spec_validate_memorysize(C):
    if len(C["mems"]) < 1:
        raise InvalidModule("invalid")
    return [], [constants.INT32]


def spec_validate_memorygrow(C):
    if len(C["mems"]) < 1:
        raise InvalidModule("invalid")
    return [constants.INT32], [constants.INT32]


# 3.3.5 CONTROL INSTRUCTIONS


def spec_validate_nop():
    return [], []


def spec_validate_uneachable():
    return ["t1*"], ["t2*"]


def spec_validate_block(C, tq, instrstar):
    C["labels"].append([tq] if tq else [])
    type_ = spec_validate_instrstar(C, instrstar)
    C["labels"].pop()
    if type_ != ([], [tq] if tq else []):
        raise InvalidModule("invalid")
    return type_


def spec_validate_loop(C, tq, instrstar):
    C["labels"].append([])
    type_ = spec_validate_instrstar(C, instrstar)
    C["labels"].pop()
    if type_ != ([], [tq] if tq else []):
        raise InvalidModule("invalid")
    return type_


def spec_validate_if(C, tq, instrstar1, instrstar2):
    C["labels"].append([tq] if tq else [])
    type_ = spec_validate_instrstar(C, instrstar1)
    if type_ != ([], [tq] if tq else []):
        raise InvalidModule("invalid")
    type_ = spec_validate_instrstar(C, instrstar2)
    if type_ != ([], [tq] if tq else []):
        raise InvalidModule("invalid")
    C["labels"].pop()
    return [constants.INT32], [tq] if tq else []


def spec_validate_br(C, l):
    if len(C["labels"]) <= l:
        raise InvalidModule("invalid")
    tq_in_brackets = C["labels"][l]
    return ["t1*"] + tq_in_brackets, ["t2*"]


def spec_validate_br_if(C, l):
    if len(C["labels"]) <= l:
        raise InvalidModule("invalid")
    tq_in_brackets = C["labels"][l]
    return tq_in_brackets + [constants.INT32], tq_in_brackets


def spec_validate_br_table(C, lstar, lN):
    if len(C["labels"]) <= lN:
        raise InvalidModule("invalid")
    tq_in_brackets = C["labels"][lN]
    for li in lstar:
        if len(C["labels"]) <= li:
            raise InvalidModule("invalid")
        if C["labels"][li] != tq_in_brackets:
            raise InvalidModule("invalid")
    return ["t1*"] + tq_in_brackes + [constants.INT32], ["t2*"]


def spec_validate_return(C):
    if C["return"] == None:
        raise InvalidModule("invalid")
    tq_in_brackets = C["return"]
    return ["t1*"] + tq_in_brackes + [constants.INT32], ["t2*"]


def spec_validate_call(C, x):
    if len(C["funcs"]) <= x:
        raise InvalidModule("invalid")
    return C["funcs"][x]


def spec_validate_call_indirect(C, x):
    if C["tables"] == None or len(C["tables"]) < 1:
        raise InvalidModule("invalid")
    limits, elemtype = C["tables"][0]
    if elemtype != "anyfunc":
        raise InvalidModule("invalid")
    if C["types"] == None or len(C["types"]) <= x:
        raise InvalidModule("invalid")
    return C["types"][x][0] + [constants.INT32], C["types"][x][1]


# 3.3.6 INSTRUCTION SEQUENCES

# We use the algorithm in the appendix for validating instruction sequences

# 3.3.7 EXPRESSIONS


def spec_validate_expr(C, expr):
    opd_stack = []
    ctrl_stack = []
    iterate_through_expression_and_validate_each_opcode(
        expr, C, opd_stack, ctrl_stack
    )  # call to the algorithm in the appendix
    if len(opd_stack) > 1:
        raise InvalidModule("invalid")
    else:
        return opd_stack


def spec_validate_const_instr(C, instr):
    if instr[0] not in {
        "i32.const",
        "i64.const",
        "f32.const",
        "f64.const",
        "get_global",
    }:
        raise InvalidModule("invalid")
    if instr[0] == "get_global" and C["globals"][instr[1]][0] != "const":
        raise InvalidModule("invalid")
    return "const"


def spec_validate_const_expr(C, expr):
    # expr is in AST form
    stack = []
    for e in expr[:-1]:
        spec_validate_const_instr(C, e)
    if expr[-1][0] != "end":
        raise InvalidModule("invalid")
    return "const"


#############
# 3.4 MODULES
#############

# 3.4.1 FUNCTIONS


def spec_validate_func(C, func, raw=None):
    x = func["type"]
    if len(C["types"]) <= x:
        raise InvalidModule("invalid")
    t1 = C["types"][x][0]
    t2 = C["types"][x][1]
    C["locals"] = t1 + func["locals"]
    C["labels"] = t2
    C["return"] = t2
    # validate body using algorithm in appendix
    instrstar = [
        ["block", t2, func["body"]]
    ]  # spec didn't nest func body in a block, but algorithm in appendix gives errors otherwise
    ft = spec_validate_expr(C, instrstar)
    # clear out function-specific things
    C["locals"] = []
    C["labels"] = []
    C["return"] = []
    return ft


# 3.4.2 TABLES


def spec_validate_table(table):
    return spec_validate_tabletype(table["type"])


# 3.4.3 MEMORIES


def spec_validate_mem(mem):
    ret = spec_validate_memtype(mem["type"])
    if mem["type"]["min"] > constants.PAGE_SIZE_64K:
        raise InvalidModule("invalid")
    if mem["type"]["max"] and mem["type"]["max"] > constants.PAGE_SIZE_64K:
        raise InvalidModule("invalid")
    return ret


# 3.4.4 GLOBALS


def spec_validate_global(C, global_):
    spec_validate_globaltype(global_["type"])
    # validate expr, but wrap it in a block first since empty control stack gives errors
    # but first wrap in block with appropriate return type
    instrstar = [["block", global_["type"][1], global_["init"]]]
    ret = spec_validate_expr(C, instrstar)
    if ret != [global_["type"][1]]:
        raise InvalidModule("invalid")
    ret = spec_validate_const_expr(C, global_["init"])
    return global_["type"]


# 3.4.5 ELEMENT SEGMENT


def spec_validate_elem(C, elem):
    x = elem["table"]
    if "tables" not in C or len(C["tables"]) <= x:
        raise InvalidModule("invalid")
    tabletype = C["tables"][x]
    limits = tabletype[0]
    elemtype = tabletype[1]
    if elemtype != "anyfunc":
        raise InvalidModule("invalid")
    # first wrap in block with appropriate return type
    instrstar = [["block", constants.INT32, elem["offset"]]]
    ret = spec_validate_expr(C, instrstar)
    if ret != [constants.INT32]:
        raise InvalidModule("invalid")
    spec_validate_const_expr(C, elem["offset"])
    for y in elem["init"]:
        if len(C["funcs"]) <= y:
            raise InvalidModule("invalid")
    return 0


# 3.4.6 DATA SEGMENTS


def spec_validate_data(C, data):
    x = data["data"]
    if len(C["mems"]) <= x:
        raise InvalidModule("invalid")
    instrstar = [["block", constants.INT32, data["offset"]]]
    ret = spec_validate_expr(C, instrstar)
    if ret != [constants.INT32]:
        raise InvalidModule("invalid")
    spec_validate_const_expr(C, data["offset"])
    return 0


# 3.4.7 START FUNCTION


def spec_validate_start(C, start):
    x = start["func"]
    if len(C["funcs"]) <= x:
        raise InvalidModule("invalid")
    if C["funcs"][x] != [[], []]:
        raise InvalidModule("invalid")
    return 0


# 3.4.8 EXPORTS


def spec_validate_export(C, export):
    return spec_validate_exportdesc(C, export["desc"])


def spec_validate_exportdesc(C, exportdesc):
    x = exportdesc[1]
    if exportdesc[0] == "func":
        if len(C["funcs"]) <= x:
            raise InvalidModule("invalid")
        return ["func", C["funcs"][x]]
    elif exportdesc[0] == "table":
        if len(C["tables"]) <= x:
            raise InvalidModule("invalid")
        return ["table", C["tables"][x]]
    elif exportdesc[0] == "mem":
        if len(C["mems"]) <= x:
            raise InvalidModule("invalid")
        return ["mem", C["mems"][x]]
    elif exportdesc[0] == "global":
        if len(C["globals"]) <= x:
            raise InvalidModule("invalid")
        mut, t = C["globals"][x]
        # TODO: verify compliance with the spec for this commented out line.
        # if mut != "const": raise InvalidModule("invalid") #TODO: this was in the spec, but tests fail linking.wast: $Mg exports a mutable global, seems not to parse in wabt
        return ["global", C["globals"][x]]
    else:
        raise InvalidModule("invalid")


# 3.4.9 IMPORTS


def spec_validate_import(C, import_):
    return spec_validate_importdesc(C, import_["desc"])


def spec_validate_importdesc(C, importdesc):
    if importdesc[0] == "func":
        x = importdesc[1]
        if len(C["funcs"]) <= x:
            raise InvalidModule("invalid")
        return ["func", C["types"][x]]
    elif importdesc[0] == "table":
        tabletype = importdesc[1]
        spec_validate_tabletype(tabletype)
        return ["table", tabletype]
    elif importdesc[0] == "mem":
        memtype = importdesc[1]
        spec_validate_memtype(memtype)
        return ["mem", memtype]
    elif importdesc[0] == "global":
        globaltype = importdesc[1]
        spec_validate_globaltype(globaltype)
        # if globaltype[0] != "const": raise InvalidModule("invalid") #TODO: this was in the spec, but tests fail linking.wast: $Mg exports a mutable global, seems not to parse in wabt
        return ["global", globaltype]
    else:
        raise InvalidModule("invalid")


# 3.4.10 MODULE


def spec_validate_module(mod):
    # mod is the module to validate
    ftstar = []
    for func in mod["funcs"]:
        if len(mod["types"]) <= func["type"]:
            # this was not explicit in spec, how about other *tstar
            raise InvalidModule("invalid")
        ftstar += [mod["types"][func["type"]]]
    ttstar = [table["type"] for table in mod["tables"]]
    mtstar = [mem["type"] for mem in mod["mems"]]
    gtstar = [global_["type"] for global_ in mod["globals"]]
    itstar = []
    for import_ in mod["imports"]:
        if import_["desc"][0] == "func":
            if len(mod["types"]) <= import_["desc"][1]:
                # this was not explicit in spec
                raise InvalidModule("invalid")
            itstar.append(["func", mod["types"][import_["desc"][1]]])
        else:
            itstar.append(import_["desc"])
    # let i_tstar be the concatenation of imports of each type
    iftstar = spec_funcs(itstar)  # [it[1] for it in itstar if it[0]=="func"]
    ittstar = spec_tables(itstar)  # [it[1] for it in itstar if it[0]=="table"]
    imtstar = spec_mems(itstar)  # [it[1] for it in itstar if it[0]=="mem"]
    igtstar = spec_globals(itstar)  # [it[1] for it in itstar if it[0]=="global"]
    # let C and Cprime be contexts
    C = {
        "types": mod["types"],
        "funcs": iftstar + ftstar,
        "tables": ittstar + ttstar,
        "mems": imtstar + mtstar,
        "globals": igtstar + gtstar,
        "locals": [],
        "labels": [],
        "return": [],
    }
    Cprime = {
        "types": [],
        "funcs": [],
        "tables": [],
        "mems": [],
        "globals": igtstar,
        "locals": [],
        "labels": [],
        "returns": [],
    }
    # et* is needed later, here is a good place to do it
    etstar = []
    for export in mod["exports"]:
        if export["desc"][0] == "func":
            if len(C["funcs"]) <= export["desc"][1]:
                # this was not explicit in spec
                raise InvalidModule("invalid")
            etstar.append(["func", C["funcs"][export["desc"][1]]])
        elif export["desc"][0] == "table":
            if len(C["tables"]) <= export["desc"][1]:
                # this was not explicit in spec
                raise InvalidModule("invalid")
            etstar.append(["table", C["tables"][export["desc"][1]]])
        elif export["desc"][0] == "mem":
            if len(C["mems"]) <= export["desc"][1]:
                # this was not explicit in spec
                raise InvalidModule("invalid")
            etstar.append(["mem", C["mems"][export["desc"][1]]])
        elif export["desc"][0] == "global":
            if len(C["globals"]) <= export["desc"][1]:
                # this was not explicit in spec
                raise InvalidModule("invalid")
            etstar.append(["global", C["globals"][export["desc"][1]]])
    # under the context C
    for functypei in mod["types"]:
        spec_validate_functype(functypei)
    for i, func in enumerate(mod["funcs"]):
        ft = spec_validate_func(C, func)
        if ft != ftstar[i][1]:
            raise InvalidModule("invalid")
    for i, table in enumerate(mod["tables"]):
        tt = spec_validate_table(table)
        if tt != ttstar[i]:
            raise InvalidModule("invalid")
    for i, mem in enumerate(mod["mems"]):
        mt = spec_validate_mem(mem)
        if mt != mtstar[i]:
            raise InvalidModule("invalid")
    for i, global_ in enumerate(mod["globals"]):
        gt = spec_validate_global(Cprime, global_)
        if gt != gtstar[i]:
            raise InvalidModule("invalid")
    for elem in mod["elem"]:
        spec_validate_elem(C, elem)
    for data in mod["data"]:
        spec_validate_data(C, data)
    if mod["start"]:
        spec_validate_start(C, mod["start"])
    for i, import_ in enumerate(mod["imports"]):
        it = spec_validate_import(C, import_)
        if it != itstar[i]:
            raise InvalidModule("invalid")
    for i, export in enumerate(mod["exports"]):
        et = spec_validate_export(C, export)
        if et != etstar[i]:
            raise InvalidModule("invalid")
    if len(C["tables"]) > 1:
        raise InvalidModule("invalid")
    if len(C["mems"]) > 1:
        raise InvalidModule("invalid")
    # export names must be unique
    exportnames = set()
    for export in mod["exports"]:
        if export["name"] in exportnames:
            raise InvalidModule("invalid")
        exportnames.add(export["name"])
    return [itstar, etstar]


###############
###############
# 4 EXECUTION #
###############
###############

# Chapter 4 defines execution semantics over the abstract syntax.


##############
# 4.3 NUMERICS
##############


def spec_trunc(q):
    logger.debug("spec_trunc(%s)", q)

    # round towards zero
    # q can be float or rational as tuple (numerator,denominator)
    if type(q) == tuple:  # rational
        result = q[0] // q[1]  # rounds towards negative infinity
        if result < 0 and q[1] * result != q[0]:
            return result + 1
        else:
            return result
    elif type(q) == float:
        # using ftrunc instead
        return int(q)


# 4.3.1 REPRESENTATIONS

# bits are string of 1s and 0s
# bytes are bytearray (maybe can also read from memoryview)


def spec_bitst(t, c):
    logger.debug("spec_bitst(%s, %s)", t, c)

    N = get_bit_size(t)

    if is_integer_type(t):
        return spec_bitsiN(N, c)
    elif is_float_type(t):
        return spec_bitsfN(N, c)
    else:
        raise Exception(f"Invariant: unknown type '{t}'")


def spec_bitst_inv(t, bits):
    logger.debug("spec_bitst_inv(%s, %s)", t, bits)

    N = get_bit_size(t)

    if is_integer_type(t):
        return spec_bitsiN_inv(N, bits)
    elif is_float_type(t):
        return spec_bitsfN_inv(N, bits)
    else:
        raise Exception(f"Invariant: unknown type '{t}'")


def spec_bitsiN(N, i):
    logger.debug("spec_bitsiN(%s, %s)", N, i)

    return spec_ibitsN(N, i)


def spec_bitsiN_inv(N, bits):
    logger.debug("spec_bitsiN_inv(%s, %s)", N, bits)

    return spec_ibitsN_inv(N, bits)


def spec_bitsfN(N, z):
    logger.debug("spec_bitsfN(%s, %s)", N, z)

    return spec_fbitsN(N, z)


def spec_bitsfN_inv(N, bits):
    logger.debug("spec_bitsfN_inv(%s, %s)", N, bits)

    return spec_fbitsN_inv(N, bits)


# Integers


def spec_ibitsN(N, i):
    logger.debug("spec_ibitsN(%s, %s)", N, i)

    return bin(i)[2:].zfill(N)


def spec_ibitsN_inv(N, bits):
    logger.debug("spec_ibitsN_inv(%s, %s)", N, bits)

    return int(bits, 2)


# Floating-Point


def spec_fbitsN(N, z):
    logger.debug("spec_fbitsN(%s, %s)", N, z)

    if N == 32:
        z_bytes = struct.pack(">f", z)
    elif N == 64:
        z_bytes = struct.pack(">d", z)
    else:
        raise Exception(f"Invariant: bit size must be one of 32/64 - Got '{N}'")

    # stryct.pack() gave us bytes, need bits
    bits = ""
    for byte in z_bytes:
        bits += bin(int(byte)).lstrip("0b").zfill(8)
    return bits


def spec_fbitsN_inv(N, bits):
    logger.debug("spec_fbitsN_inv(%s, %s)", N, bits)

    # will use struct.unpack() so need bytearray
    bytes_ = bytearray()
    for i in range(len(bits) // 8):
        bytes_ += bytearray([int(bits[8 * i : 8 * (i + 1)], 2)])
    if N == 32:
        z = struct.unpack(">f", bytes_)[0]
    elif N == 64:
        z = struct.unpack(">d", bytes_)[0]
    return z


def spec_fsign(z):
    logger.debug("spec_fsign(%s)", z)

    bytes_ = spec_bytest(constants.FLOAT64, z)
    sign = bytes_[-1] & 0b10000000  # -1 since littleendian
    if sign:
        return 1
    else:
        return 0


# decided to just use struct.pack() and struct.unpack()
# other options to represent floating point numbers:
#   float which is 64-bit, for 32-bit, can truncate significand and exponent after each operation
#   ctypes.c_float and ctypes.c_double
#   numpy.float32 and numpy.float64


# Storage


def spec_bytest(t, i):
    logger.debug("spec_bytest(%s, %s)", t, i)

    if is_integer_type(t):
        bits = spec_bitsiN(get_bit_size(t), i)
    elif is_float_type(t):
        bits = spec_bitsfN(get_bit_size(t), i)
    else:
        raise Exception(f"Invariant: unknown type '{t}'")

    return spec_littleendian(bits)


def spec_bytest_inv(t, bytes_):
    logger.debug("spec_bytest_inv(%s, %s)", t, bytes_)

    bits = spec_littleendian_inv(bytes_)

    if is_integer_type(t):
        return spec_bitsiN_inv(get_bit_size(t), bits)
    elif is_float_type(t):
        return spec_bitsfN_inv(get_bit_size(t), bits)
    else:
        raise Exception(f"Invariant: unknown type '{t}'")


def spec_bytesiN(N, i):
    logger.debug("spec_bytesiN(%s, %s)", N, i)

    bits = spec_bitsiN(N, i)
    # convert bits to bytes
    bytes_ = bytearray()
    for byteIdx in range(0, len(bits), 8):
        bytes_ += bytearray([int(bits[byteIdx : byteIdx + 8], 2)])
    return bytes_


def spec_bytesiN_inv(N, bytes_):
    logger.debug("spec_bytesiN_inv(%s, %s)", N, bytes_)

    bits = ""
    for byte in bytes_:
        bits += spec_ibitsN(8, byte)
    return spec_ibitsN_inv(N, bits)


# TODO: these are unused, but might use when refactor floats to pass NaN significand tests
def spec_bytesfN(N, z):
    logger.debug("spec_bytesfN(%s, %s)", N, z)

    if N == 32:
        z_bytes = struct.pack(">f", z)
    elif N == 64:
        z_bytes = struct.pack(">d", z)
    else:
        raise Exception(f"Invariant: bit size must be one of 32/64 - Got '{N}'")

    return z_bytes


def spec_bytesfN_inv(N, bytes_):
    logger.debug("spec_bytesfN_inv(%s, %s)", N, bytes_)

    if N == 32:
        z = struct.unpack(">f", bytes_)[0]
    elif N == 64:
        z = struct.unpack(">d", bytes_)[0]
    else:
        raise Exception(f"Invariant: bit size must be one of 32/64 - Got '{N}'")

    return z


def spec_littleendian(d):
    logger.debug("spec_littleendian(%s)", d)

    # same behavior for both 32 and 64-bit values
    # this assumes len(d) is divisible by 8
    if len(d) == 0:
        return bytearray()
    d18 = d[:8]
    d2Nm8 = d[8:]
    d18_as_int = spec_ibitsN_inv(8, d18)
    return spec_littleendian(d2Nm8) + bytearray([d18_as_int])


def spec_littleendian_inv(bytes_):
    logger.debug("spec_littleendian_inv(%s)", bytes_)

    # same behavior for both 32 and 64-bit values
    # this assumes len(d) is divisible by 8
    # this converts bytes to bits
    if len(bytes_) == 0:
        return ""
    bits = bin(int(bytes_[-1])).lstrip("0b").zfill(8)
    return bits + spec_littleendian_inv(bytes_[:-1])


# 4.3.2 INTEGER OPERATIONS


# two's comlement
def spec_signediN(N, i):
    """
    TODO: see if this is faster
    return i - int((i << 1) & 2**N) #https://stackoverflow.com/a/36338336
    """
    logger.debug("spec_signediN(%s, %s)", N, i)

    if 0 <= i < 2 ** (N - 1):
        return i
    elif 2 ** (N - 1) <= i < 2 ** N:
        return i - 2 ** N
    else:
        raise Exception(f"Invariant: bit size out of range - Got '{N}'")


def spec_signediN_inv(N, i):
    logger.debug("spec_signediN_inv(%s, %s)", N, i)

    if 0 <= i < 2 ** (N - 1):
        return i
    elif -1 * (2 ** (N - 1)) <= i < 0:
        return i + 2 ** N
    else:
        raise Exception(f"Invariant: bit size out of range - Got '{N}'")


def spec_iaddN(N, i1, i2):
    logger.debug("spec_iaddN(%s, %s, %s)", N, i1, i2)

    return (i1 + i2) % 2 ** N


def spec_isubN(N, i1, i2):
    logger.debug("spec_isubN(%s, %s, %s)", N, i1, i2)

    return (i1 - i2 + 2 ** N) % 2 ** N


def spec_imulN(N, i1, i2):
    logger.debug("spec_imulN(%s, %s, %s)", N, i1, i2)

    return (i1 * i2) % 2 ** N


def spec_idiv_uN(N, i1, i2):
    logger.debug("spec_idiv_uN(%s, %s, %s)", N, i1, i2)

    if i2 == 0:
        raise Trap("trap")
    return spec_trunc((i1, i2))


def spec_idiv_sN(N, i1, i2):
    logger.debug("spec_idiv_sN(%s, %s, %s)", N, i1, i2)

    j1 = spec_signediN(N, i1)
    j2 = spec_signediN(N, i2)
    if j2 == 0:
        raise Trap("trap")
    # assuming j1 and j2 are N-bit
    if j1 // j2 == 2 ** (N - 1):
        raise Trap("trap")
    return spec_signediN_inv(N, spec_trunc((j1, j2)))


def spec_irem_uN(N, i1, i2):
    logger.debug("spec_irem_uN(%s, %s, %s)", N, i1, i2)

    if i2 == 0:
        raise Trap("trap")
    return i1 - i2 * spec_trunc((i1, i2))


def spec_irem_sN(N, i1, i2):
    logger.debug("spec_irem_sN(%s, %s, %s)", N, i1, i2)

    j1 = spec_signediN(N, i1)
    j2 = spec_signediN(N, i2)
    if i2 == 0:
        raise Trap("trap")
    return spec_signediN_inv(N, j1 - j2 * spec_trunc((j1, j2)))


def spec_iandN(N, i1, i2):
    logger.debug("spec_iandN(%s, %s, %s)", N, i1, i2)

    return i1 & i2


def spec_iorN(N, i1, i2):
    logger.debug("spec_iorN(%s, %s, %s)", N, i1, i2)

    return i1 | i2


def spec_ixorN(N, i1, i2):
    logger.debug("spec_ixorN(%s, %s, %s)", N, i1, i2)

    return i1 ^ i2


def spec_ishlN(N, i1, i2):
    logger.debug("spec_ishlN(%s, %s, %s)", N, i1, i2)

    k = i2 % N
    return (i1 << k) % (2 ** N)


def spec_ishr_uN(N, i1, i2):
    logger.debug("spec_ishr_uN(%s, %s, %s)", N, i1, i2)

    j2 = i2 % N
    return i1 >> j2


def spec_ishr_sN(N, i1, i2):
    logger.debug("spec_ishr_sN(%s, %s, %s)", N, i1, i2)

    k = i2 % N
    d0d1Nmkm1d2k = spec_ibitsN(N, i1)
    d0 = d0d1Nmkm1d2k[0]
    d1Nmkm1 = d0d1Nmkm1d2k[1 : N - k]
    return spec_ibitsN_inv(N, d0 * (k + 1) + d1Nmkm1)


def spec_irotlN(N, i1, i2):
    logger.debug("spec_irotlN(%s, %s, %s)", N, i1, i2)

    k = i2 % N
    d1kd2Nmk = spec_ibitsN(N, i1)
    d2Nmk = d1kd2Nmk[k:]
    d1k = d1kd2Nmk[:k]
    return spec_ibitsN_inv(N, d2Nmk + d1k)


def spec_irotrN(N, i1, i2):
    logger.debug("spec_irotrN(%s, %s, %s)", N, i1, i2)

    k = i2 % N
    d1Nmkd2k = spec_ibitsN(N, i1)
    d1Nmk = d1Nmkd2k[: N - k]
    d2k = d1Nmkd2k[N - k :]
    return spec_ibitsN_inv(N, d2k + d1Nmk)


def spec_iclzN(N, i):
    logger.debug("spec_iclzN(%s, %s)", N, i)

    k = 0
    for b in spec_ibitsN(N, i):
        if b == "0":
            k += 1
        else:
            break
    return k


def spec_ictzN(N, i):
    logger.debug("spec_ictzN(%s, %s)", N, i)

    k = 0
    for b in reversed(spec_ibitsN(N, i)):
        if b == "0":
            k += 1
        else:
            break
    return k


def spec_ipopcntN(N, i):
    logger.debug("spec_ipopcntN(%s, %s)", N, i)

    k = 0
    for b in spec_ibitsN(N, i):
        if b == "1":
            k += 1
    return k


def spec_ieqzN(N, i):
    logger.debug("spec_ieqzN(%s, %s)", N, i)

    if i == 0:
        return 1
    else:
        return 0


def spec_ieqN(N, i1, i2):
    logger.debug("spec_ieqN(%s, %s, %s)", N, i1, i2)

    if i1 == i2:
        return 1
    else:
        return 0


def spec_ineN(N, i1, i2):
    logger.debug("spec_ineN(%s, %s, %s)", N, i1, i2)

    if i1 != i2:
        return 1
    else:
        return 0


def spec_ilt_uN(N, i1, i2):
    logger.debug("spec_ilt_uN(%s, %s, %s)", N, i1, i2)

    if i1 < i2:
        return 1
    else:
        return 0


def spec_ilt_sN(N, i1, i2):
    logger.debug("spec_ilt_sN(%s, %s, %s)", N, i1, i2)

    j1 = spec_signediN(N, i1)
    j2 = spec_signediN(N, i2)
    if j1 < j2:
        return 1
    else:
        return 0


def spec_igt_uN(N, i1, i2):
    logger.debug("spec_igt_uN(%s, %s, %s)", N, i1, i2)

    if i1 > i2:
        return 1
    else:
        return 0


def spec_igt_sN(N, i1, i2):
    logger.debug("spec_igt_sN(%s, %s, %s)", N, i1, i2)

    j1 = spec_signediN(N, i1)
    j2 = spec_signediN(N, i2)
    if j1 > j2:
        return 1
    else:
        return 0


def spec_ile_uN(N, i1, i2):
    logger.debug("spec_ile_uN(%s, %s, %s)", N, i1, i2)

    if i1 <= i2:
        return 1
    else:
        return 0


def spec_ile_sN(N, i1, i2):
    logger.debug("spec_ile_sN(%s, %s, %s)", N, i1, i2)

    j1 = spec_signediN(N, i1)
    j2 = spec_signediN(N, i2)
    if j1 <= j2:
        return 1
    else:
        return 0


def spec_ige_uN(N, i1, i2):
    logger.debug("spec_ige_uN(%s, %s, %s)", N, i1, i2)

    if i1 >= i2:
        return 1
    else:
        return 0


def spec_ige_sN(N, i1, i2):
    logger.debug("spec_ige_sN(%s, %s, %s)", N, i1, i2)

    j1 = spec_signediN(N, i1)
    j2 = spec_signediN(N, i2)
    if j1 >= j2:
        return 1
    else:
        return 0


# 4.3.3 FLOATING-POINT OPERATIONS


def spec_fabsN(N, z):
    logger.debug("spec_fabsN(%s, %s)", N, z)

    sign = spec_fsign(z)
    if sign == 0:
        return z
    else:
        return spec_fnegN(N, z)


def spec_fnegN(N, z):
    logger.debug("spec_fnegN(%s, %s)", N, z)

    # get bytes and sign
    bytes_ = spec_bytest(constants.FLOAT64, z)  # 64 since errors if z too bit for 32
    sign = spec_fsign(z)
    if sign == 0:
        bytes_[-1] |= 0b10000000  # -1 since littleendian
    else:
        bytes_[-1] &= 0b01111111  # -1 since littleendian
    z = spec_bytest_inv(constants.FLOAT64, bytes_)  # 64 since errors if z too bit for 32
    return z


def spec_fceilN(N, z):
    logger.debug("spec_fceilN(%s, %s)", N, z)

    if math.isnan(z):
        return z
    elif math.isinf(z):
        return z
    elif z == 0:
        return z
    elif -1.0 < z < 0.0:
        return -0.0
    else:
        return float(math.ceil(z))


def spec_ffloorN(N, z):
    logger.debug("spec_ffloorN(%s, %s)", N, z)

    if math.isnan(z):
        return z
    elif math.isinf(z):
        return z
    elif z == 0:
        return z
    elif 0.0 < z < 1.0:
        return 0.0
    else:
        return float(math.floor(z))


def spec_ftruncN(N, z):
    logger.debug("spec_ftruncN(%s, %s)", N, z)

    if math.isnan(z):
        return z
    elif math.isinf(z):
        return z
    elif z == 0:
        return z
    elif 0.0 < z < 1.0:
        return 0.0
    elif -1.0 < z < 0.0:
        return -0.0
    else:
        magnitude = spec_fabsN(N, z)
        floormagnitude = spec_ffloorN(N, magnitude)
        return floormagnitude * (
            -1 if spec_fsign(z) else 1
        )  # math.floor(z)) + spec_fsign(z)


def spec_fnearestN(N, z):
    logger.debug("spec_fnearestN(%s, %s)", N, z)

    if math.isnan(z):
        return z
    elif math.isinf(z):
        return z
    elif z == 0:
        return z
    elif 0.0 < z <= 0.5:
        return 0.0
    elif -0.5 <= z < 0.0:
        return -0.0
    else:
        return float(round(z))


def spec_fsqrtN(N, z):
    logger.debug("spec_fsqrtN(%s, %s)", N, z)

    if math.isnan(z) or (z != 0 and spec_fsign(z) == 1):
        return math.nan
    else:
        return math.sqrt(z)


def spec_faddN(N, z1, z2):
    logger.debug("spec_faddN(%s, %s, %s)", N, z1, z2)

    res = z1 + z2
    if N == 32:
        res = spec_demoteMN(64, 32, res)
    return res


def spec_fsubN(N, z1, z2):
    logger.debug("spec_fsubN(%s, %s, %s)", N, z1, z2)

    res = z1 - z2
    if N == 32:
        res = spec_demoteMN(64, 32, res)
    return res


def spec_fmulN(N, z1, z2):
    logger.debug("spec_fmulN(%s, %s, %s)", N, z1, z2)

    res = z1 * z2
    if N == 32:
        res = spec_demoteMN(64, 32, res)
    return res


def spec_fdivN(N, z1, z2):
    logger.debug("spec_fdivN(%s, %s, %s)", N, z1, z2)

    if math.isnan(z1):
        return z1
    elif math.isnan(z2):
        return z2
    elif math.isinf(z1) and math.isinf(z2):
        return math.nan
    elif z1 == 0.0 and z2 == 0.0:
        return math.nan
    elif z1 == 0.0 and z2 == 0.0:
        return math.nan
    elif math.isinf(z1):
        if spec_fsign(z1) == spec_fsign(z2):
            return math.inf
        else:
            return -math.inf
    elif math.isinf(z2):
        if spec_fsign(z1) == spec_fsign(z2):
            return 0.0
        else:
            return -0.0
    elif z1 == 0:
        if spec_fsign(z1) == spec_fsign(z2):
            return 0.0
        else:
            return -0.0
    elif z2 == 0:
        if spec_fsign(z1) == spec_fsign(z2):
            return math.inf
        else:
            return -math.inf
    else:
        res = z1 / z2
        if N == 32:
            res = spec_demoteMN(64, 32, res)
        return res


def spec_fminN(N, z1, z2):
    logger.debug("spec_fminN(%s, %s, %s)", N, z1, z2)

    if math.isnan(z1):
        return z1
    elif math.isnan(z2):
        return z2
    elif z1 == -math.inf or z2 == -math.inf:
        return -math.inf
    elif z1 == math.inf:
        return z2
    elif z2 == math.inf:
        return z1
    elif z1 == z2 == 0.0:
        if spec_fsign(z1) != spec_fsign(z2):
            return -0.0
        else:
            return z1
    elif z1 <= z2:
        return z1
    else:
        return z2


def spec_fmaxN(N, z1, z2):
    logger.debug("spec_fmaxN(%s, %s, %s)", N, z1, z2)

    if math.isnan(z1):
        return z1
    elif math.isnan(z2):
        return z2
    elif z1 == math.inf or z2 == math.inf:
        return math.inf
    elif z1 == -math.inf:
        return z2
    elif z2 == -math.inf:
        return z1
    elif z1 == z2 == 0.0:
        if spec_fsign(z1) != spec_fsign(z2):
            return 0.0
        else:
            return z1
    elif z1 <= z2:
        return z2
    else:
        return z1


def spec_fcopysignN(N, z1, z2):
    logger.debug("spec_fcopysignN(%s, %s, %s)", N, z1, z2)

    z1sign = spec_fsign(z1)
    z2sign = spec_fsign(z2)
    if z1sign == z2sign:
        return z1
    else:
        z1bytes = spec_bytest(get_float_type(N), z1)
        if z1sign == 0:
            z1bytes[-1] |= 0b10000000  # -1 since littleendian
        else:
            z1bytes[-1] &= 0b01111111  # -1 since littleendian
        z1 = spec_bytest_inv(get_float_type(N), z1bytes)
        return z1


def spec_feqN(N, z1, z2):
    logger.debug("spec_feqN(%s, %s, %s)", N, z1, z2)

    if z1 == z2:
        return 1
    else:
        return 0


def spec_fneN(N, z1, z2):
    logger.debug("spec_fneN(%s, %s, %s)", N, z1, z2)

    if z1 != z2:
        return 1
    else:
        return 0


def spec_fltN(N, z1, z2):
    logger.debug("spec_fltN(%s, %s, %s)", N, z1, z2)

    if math.isnan(z1):
        return 0
    elif math.isnan(z2):
        return 0
    elif spec_bitsfN(N, z1) == spec_bitsfN(N, z2):
        return 0
    elif z1 == math.inf:
        return 0
    elif z1 == -math.inf:
        return 1
    elif z2 == math.inf:
        return 1
    elif z2 == -math.inf:
        return 0
    elif z1 == z2 == 0:
        return 0
    elif z1 < z2:
        return 1
    else:
        return 0


def spec_fgtN(N, z1, z2):
    logger.debug("spec_fgtN(%s, %s, %s)", N, z1, z2)

    if math.isnan(z1):
        return 0
    elif math.isnan(z2):
        return 0
    elif spec_bitsfN(N, z1) == spec_bitsfN(N, z2):
        return 0
    elif z1 == math.inf:
        return 1
    elif z1 == -math.inf:
        return 0
    elif z2 == math.inf:
        return 0
    elif z2 == -math.inf:
        return 1
    elif z1 == z2 == 0:
        return 0
    elif z1 > z2:
        return 1
    else:
        return 0


def spec_fleN(N, z1, z2):
    logger.debug("spec_fleN(%s, %s, %s)", N, z1, z2)

    if math.isnan(z1):
        return 0
    elif math.isnan(z2):
        return 0
    elif spec_bitsfN(N, z1) == spec_bitsfN(N, z2):
        return 1
    elif z1 == math.inf:
        return 0
    elif z1 == -math.inf:
        return 1
    elif z2 == math.inf:
        return 1
    elif z2 == -math.inf:
        return 0
    elif z1 == z2 == 0:
        return 1
    elif z1 <= z2:
        return 1
    else:
        return 0


def spec_fgeN(N, z1, z2):
    logger.debug("spec_fgeN(%s, %s, %s)", N, z1, z2)

    if math.isnan(z1):
        return 0
    elif math.isnan(z2):
        return 0
    elif spec_bitsfN(N, z1) == spec_bitsfN(N, z2):
        return 1
    elif z1 == math.inf:
        return 1
    elif z1 == -math.inf:
        return 0
    elif z2 == math.inf:
        return 0
    elif z2 == -math.inf:
        return 1
    elif z1 == z2 == 0:
        return 1
    elif z1 >= z2:
        return 1
    else:
        return 0


# 4.3.4 CONVERSIONS


def spec_extend_uMN(M, N, i):
    logger.debug("spec_extend_uMN(%s, %s, %s)", M, N, i)

    # TODO: confirm this implementation is correct.
    return i


def spec_extend_sMN(M, N, i):
    logger.debug("spec_extend_sMN(%s, %s, %s)", M, N, i)

    j = spec_signediN(M, i)
    return spec_signediN_inv(N, j)


def spec_wrapMN(M, N, i):
    logger.debug("spec_wrapMN(%s, %s, %s)", M, N, i)

    return i % (2 ** N)


def spec_trunc_uMN(M, N, z):
    logger.debug("spec_trunc_uMN(%s, %s, %s)", M, N, z)

    if math.isnan(z) or math.isinf(z):
        raise Trap("trap")

    ztrunc = spec_ftruncN(M, z)

    if -1 < ztrunc < 2 ** N:
        return int(ztrunc)
    else:
        raise Trap("trap")


def spec_trunc_sMN(M, N, z):
    logger.debug("spec_trunc_sMN(%s, %s, %s)", M, N, z)

    if math.isnan(z) or math.isinf(z):
        raise Trap("trap")

    ztrunc = spec_ftruncN(M, z)

    if -(2 ** (N - 1)) - 1 < ztrunc < 2 ** (N - 1):
        iztrunc = int(ztrunc)
        if iztrunc < 0:
            return spec_signediN_inv(N, iztrunc)
        else:
            return iztrunc
    else:
        raise Trap("trap")


def spec_promoteMN(M, N, z):
    logger.debug("spec_promoteMN(%s, %s, %s)", M, N, z)

    # TODO: confirm this implementation is correct.
    return z


def spec_demoteMN(M, N, z):
    logger.debug("spec_demoteMN(%s, %s, %s)", M, N, z)

    absz = spec_fabsN(N, z)
    # limitN = 2**(2**(spec_expon(N)-1))
    # TODO: confirm this implementation is correct.
    limitN = constants.UINT128_CEIL * (
        1 - 2 ** -25
    )  # this FLT_MAX is slightly different than the Wasm spec's 2**127
    if absz >= limitN:
        signz = spec_fsign(z)
        if signz:
            return -math.inf
        else:
            return math.inf
    bytes_ = spec_bytest(constants.FLOAT32, z)
    z32 = spec_bytest_inv(constants.FLOAT32, bytes_)
    return z32


def spec_convert_uMN(M, N, i):
    logger.debug("spec_convert_uMN(%s, %s, %s)", M, N, i)

    limitN = 2 ** (2 ** (spec_expon(N) - 1))
    if i >= limitN:
        return math.inf
    return float(i)


def spec_convert_sMN(M, N, i):
    logger.debug("spec_convert_sMN(%s, %s, %s)", M, N, i)

    limitN = 2 ** (2 ** (spec_expon(N) - 1))

    if i >= limitN:
        return math.inf
    elif i <= -1 * limitN:
        return -math.inf
    else:
        i = spec_signediN(M, i)
        return float(i)


def spec_reinterprett1t2(t1, t2, c):
    logger.debug("spec_reinterprett1t2(%s, %s, %s)", t1, t2, c)

    bits = spec_bitst(t1, c)
    return spec_bitst_inv(t2, bits)


##################
# 4.4 INSTRUCTIONS
##################

# S is the store

# 4.4.1 NUMERIC INSTRUCTIONS


def spec_tconst(config):
    S = config["S"]
    c = config["instrstar"][config["idx"]][1]

    logger.debug("spec_tconst(%s)", c)

    config["operand_stack"] += [c]
    config["idx"] += 1


def spec_tunop(config):
    logger.debug("spec_tunop()")

    S = config["S"]
    instr = config["instrstar"][config["idx"]][0]
    t = instr[0:3]
    op = opcode2exec[instr][1]
    c1 = config["operand_stack"].pop()
    c = op(get_bit_size(t), c1)

    config["operand_stack"].append(c)
    config["idx"] += 1


def spec_tbinop(config):
    logger.debug("spec_tbinop()")

    S = config["S"]
    instr = config["instrstar"][config["idx"]][0]
    t = instr[0:3]
    op = opcode2exec[instr][1]
    c2 = config["operand_stack"].pop()
    c1 = config["operand_stack"].pop()
    c = op(get_bit_size(t), c1, c2)

    config["operand_stack"].append(c)
    config["idx"] += 1


def spec_ttestop(config):
    logger.debug("spec_ttestop()")

    S = config["S"]
    instr = config["instrstar"][config["idx"]][0]
    t = instr[0:3]
    op = opcode2exec[instr][1]
    c1 = config["operand_stack"].pop()
    c = op(get_bit_size(t), c1)

    config["operand_stack"].append(c)
    config["idx"] += 1


def spec_trelop(config):
    logger.debug("spec_trelop()")

    S = config["S"]
    instr = config["instrstar"][config["idx"]][0]
    t = instr[0:3]
    op = opcode2exec[instr][1]
    c2 = config["operand_stack"].pop()
    c1 = config["operand_stack"].pop()
    c = op(get_bit_size(t), c1, c2)

    config["operand_stack"].append(c)
    config["idx"] += 1


def spec_t2cvtopt1(config):
    logger.debug("spec_t2cvtopt1()")

    S = config["S"]
    instr = config["instrstar"][config["idx"]][0]
    t2 = instr[0:3]
    t1 = instr[-3:]
    op = opcode2exec[instr][1]
    c1 = config["operand_stack"].pop()
    if instr[4:15] == "reinterpret":
        c2 = op(t1, t2, c1)
    else:
        c2 = op(int(t1[1:]), int(t2[1:]), c1)

    config["operand_stack"].append(c2)
    config["idx"] += 1


# 4.4.2 PARAMETRIC INSTRUCTIONS


def spec_drop(config):
    logger.debug("spec_drop()")

    S = config["S"]
    config["operand_stack"].pop()
    config["idx"] += 1


def spec_select(config):
    logger.debug("spec_select()")

    S = config["S"]
    operand_stack = config["operand_stack"]
    c = operand_stack.pop()
    val1 = operand_stack.pop()
    val2 = operand_stack.pop()
    if not c:
        operand_stack.append(val1)
    else:
        operand_stack.append(val2)
    config["idx"] += 1


# 4.4.3 VARIABLE INSTRUCTIONS


def spec_get_local(config):
    logger.debug("spec_get_local()")

    S = config["S"]
    F = config["F"]
    x = config["instrstar"][config["idx"]][1]
    val = F[-1]["locals"][x]
    config["operand_stack"].append(val)
    config["idx"] += 1


def spec_set_local(config):
    logger.debug("spec_set_local()")

    S = config["S"]
    F = config["F"]
    x = config["instrstar"][config["idx"]][1]
    val = config["operand_stack"].pop()
    F[-1]["locals"][x] = val
    config["idx"] += 1


def spec_tee_local(config):
    logger.debug("spec_tee_local()")

    S = config["S"]
    x = config["instrstar"][config["idx"]][1]
    operand_stack = config["operand_stack"]
    val = operand_stack.pop()
    operand_stack.append(val)
    operand_stack.append(val)
    spec_set_local(config)
    # TODO: confirm that this should be commented out.
    # config["idx"] += 1


def spec_get_global(config):
    logger.debug("spec_get_global()")

    S = config["S"]
    F = config["F"]
    x = config["instrstar"][config["idx"]][1]
    a = F[-1]["module"]["globaladdrs"][x]
    glob = S["globals"][a]
    # TODO: confirm this spec difference and remedy
    val = glob["value"][
        1
    ]  # *** omit the type eg 'i32.const', just get the value, see above for how this is different from the spec
    config["operand_stack"].append(val)
    config["idx"] += 1


def spec_set_global(config):
    logger.debug("spec_set_global()")

    S = config["S"]
    F = config["F"]
    x = config["instrstar"][config["idx"]][1]
    a = F[-1]["module"]["globaladdrs"][x]
    glob = S["globals"][a]
    val = config["operand_stack"].pop()
    glob["value"][1] = val
    config["idx"] += 1


# 4.4.4 MEMORY INSTRUCTIONS

# this is for both t.load and t.loadN_sx
def spec_tload(config):
    logger.debug("spec_tload()")

    S = config["S"]
    F = config["F"]
    instr = config["instrstar"][config["idx"]][0]
    memarg = config["instrstar"][config["idx"]][1]
    t = instr[:3]
    # 3
    a = F[-1]["module"]["memaddrs"][0]
    # 5
    mem = S["mems"][a]
    # 7
    i = config["operand_stack"].pop()
    # 8
    ea = i + memarg["offset"]
    # 9
    sxflag = False
    if instr[3:] != ".load":  # N is part of the opcode eg i32.load8_s has N=8
        if instr[-1] == "s":
            sxflag = True
        N = int(instr[8:10].strip("_"))
    else:
        N = get_bit_size(t)
    # 10
    if ea + N // 8 > len(mem["data"]):
        raise Trap("trap")
    # 11
    bstar = mem["data"][ea : ea + N // 8]
    # 12
    if sxflag:
        n = spec_bytest_inv(t, bstar)
        c = spec_extend_sMN(N, get_bit_size(t), n)
    else:
        c = spec_bytest_inv(t, bstar)
    # 13
    config["operand_stack"].append(c)
    logger.debug("loaded %s from memory locations %s to %s", c, ea, ea + N // 8)
    config["idx"] += 1


def spec_tstore(config):
    logger.debug("spec_tstore()")

    S = config["S"]
    F = config["F"]
    instr = config["instrstar"][config["idx"]][0]
    memarg = config["instrstar"][config["idx"]][1]
    t = instr[:3]
    # 3
    a = F[-1]["module"]["memaddrs"][0]
    # 5
    mem = S["mems"][a]
    # 7
    c = config["operand_stack"].pop()
    # 9
    i = config["operand_stack"].pop()
    # 10
    ea = i + memarg["offset"]
    # 11
    Nflag = False
    if instr[3:] != ".store":  # N is part of the instruction, eg i32.store8
        Nflag = True
        N = int(instr[9:])
    else:
        N = get_bit_size(t)
    # 12
    if ea + N // 8 > len(mem["data"]):
        raise Trap("trap")
    # 13
    if Nflag:
        M = get_bit_size(t)
        c = spec_wrapMN(M, N, c)
        bstar = spec_bytest(t, c)
    else:
        bstar = spec_bytest(t, c)
    # 15
    mem["data"][ea : ea + N // 8] = bstar[: N // 8]
    logger.debug("stored %s to memory locations %s to %s", bstar[:N//8], ea, ea + N // 8)
    config["idx"] += 1


def spec_memorysize(config):
    logger.debug("spec_memorysize()")

    S = config["S"]
    F = config["F"]
    a = F[-1]["module"]["memaddrs"][0]
    mem = S["mems"][a]
    sz = len(mem["data"]) // constants.PAGE_SIZE_64K
    config["operand_stack"].append(sz)
    config["idx"] += 1


def spec_memorygrow(config):
    logger.debug("spec_memorygrow()")

    S = config["S"]
    F = config["F"]
    a = F[-1]["module"]["memaddrs"][0]
    mem = S["mems"][a]
    sz = len(mem["data"]) // constants.PAGE_SIZE_64K
    n = config["operand_stack"].pop()
    spec_growmem(mem, n)
    if sz + n == len(mem["data"]) // constants.PAGE_SIZE_64K:  # success
        config["operand_stack"].append(sz)
    else:
        # TODO: this potentially ends up leaving the memory in an invalid state
        config["operand_stack"].append(constants.INT32_NEGATIVE_ONE)  # put -1 on top of stack
    config["idx"] += 1


# 4.4.5 CONTROL INSTRUCTIONS


"""
 This implementation deviates from the spec as follows.
   - Three stacks are maintained, operands, control-flow labels, and function-call frames.
     Operand_stack holds only values, control_stack holds only labels. The function-call frames are mainted implicitly in Python function calls -- this will be changed, putting function call frames into the label stack or into their own stack.
   - `config` inculdes store S, frame F, instr_list, idx into this instr_list, operand_stack, and control_stack.
   - Each label L has extra value for height of operand stack when it started, continuation when it is branched to, and end when it's last instruction is called.
"""


def spec_nop(config):
    logger.debug("spec_nop()")

    config["idx"] += 1


def spec_unreachable(config):
    logger.debug("spec_unreachable()")

    raise Trap("trap")


def spec_block(config):
    logger.debug("spec_block()")

    instrstar = config["instrstar"]
    idx = config["idx"]
    operand_stack = config["operand_stack"]
    control_stack = config["control_stack"]
    t = instrstar[idx][1]
    # 1
    if type(t) == str:
        n = 1
    elif type(t) == list:
        n = len(t)
    # 2
    continuation = [instrstar, idx + 1]
    L = {
        "arity": n,
        "height": len(operand_stack),
        "continuation": continuation,
        "end": continuation,
    }
    # 3
    spec_enter_block(config, instrstar[idx][2], L)
    # control_stack.append(L)
    # config["instrstar"] = instrstar[idx][2]
    # config["idx"] = 0


def spec_loop(config):
    logger.debug("spec_loop()")

    instrstar = config["instrstar"]
    idx = config["idx"]
    operand_stack = config["operand_stack"]
    control_stack = config["control_stack"]
    # 1
    continuation = [instrstar[idx][2], 0]
    end = [instrstar, idx + 1]
    L = {
        "arity": 0,
        "height": len(operand_stack),
        "continuation": continuation,
        "end": end,
        "loop_flag": 1,
    }
    # 2
    spec_enter_block(config, instrstar[idx][2], L)
    # control_stack.append(L)
    # config["instrstar"] = instrstar[idx][2]
    # config["idx"] = 0


def spec_if(config):
    logger.debug("spec_if()")

    instrstar = config["instrstar"]
    idx = config["idx"]
    operand_stack = config["operand_stack"]
    control_stack = config["control_stack"]
    # 2
    c = operand_stack.pop()
    # 3
    t = instrstar[idx][1]
    if type(t) == str:
        n = 1
    elif type(t) == list:
        n = len(t)
    # 4
    continuation = [instrstar, idx + 1]
    L = {
        "arity": n,
        "height": len(operand_stack),
        "continuation": continuation,
        "end": continuation,
    }
    # 5
    if c:
        spec_enter_block(config, instrstar[idx][2], L)
    # 6
    else:
        spec_enter_block(config, instrstar[idx][3], L)


def spec_br(config, l=None):
    logger.debug('spec_br()')

    operand_stack = config["operand_stack"]
    control_stack = config["control_stack"]
    if l == None:
        l = config["instrstar"][config["idx"]][1]
    # 2
    L = control_stack[-1 * (l + 1)]
    # 3
    n = L["arity"]
    # 5
    valn = []
    if n > 0:
        valn = operand_stack[-1 * n :]
    # 6
    del operand_stack[L["height"] :]
    if (
        "loop_flag" in L
    ):  # branching to loop starts at beginning of loop, so don't delete
        if l > 0:
            del control_stack[-1 * l :]
        config["idx"] = 0
    else:
        del control_stack[-1 * (l + 1) :]
    # 7
    operand_stack += valn
    # 8
    config["instrstar"], config["idx"] = L["continuation"]


def spec_br_if(config):
    logger.debug('spec_br_if()')

    l = config["instrstar"][config["idx"]][1]
    # 2
    c = config["operand_stack"].pop()
    # 3
    if c != 0:
        spec_br(config, l)
    # 4
    else:
        config["idx"] += 1


def spec_br_table(config):
    logger.debug('spec_br_table()')

    lstar = config["instrstar"][config["idx"]][1]
    lN = config["instrstar"][config["idx"]][2]
    # 2
    i = config["operand_stack"].pop()
    # 3
    if i < len(lstar):
        li = lstar[i]
        spec_br(config, li)
    # 4
    else:
        spec_br(config, lN)


def spec_return(config):
    logger.debug('spec_return()')

    operand_stack = config["operand_stack"]
    # 1
    F = config["F"][-1]
    # 2
    n = F["arity"]
    # 4
    valn = []
    if n > 0:
        valn = operand_stack[-1 * n :]
        # 6
        del operand_stack[F["height"] :]
    # 8
    config["F"].pop()
    # 9
    operand_stack += valn
    config["instrstar"], config["idx"], config["control_stack"] = F["continuation"]


def spec_call(config):
    logger.debug('spec_call()')

    operand_stack = config["operand_stack"]
    instr = config["instrstar"][config["idx"]]
    x = instr[1]
    # 1
    F = config["F"][-1]
    # 3
    a = F["module"]["funcaddrs"][x]
    # 4
    ret = spec_invoke_function_address(config, a)


def spec_call_indirect(config):
    logger.debug('spec_call_indirect()')

    S = config["S"]
    # 1
    F = config["F"][-1]
    # 3
    ta = F["module"]["tableaddrs"][0]
    # 5
    tab = S["tables"][ta]
    # 7
    x = config["instrstar"][config["idx"]][1]
    ftexpect = F["module"]["types"][x]
    # 9
    i = config["operand_stack"].pop()
    # 10
    if len(tab["elem"]) <= i:
        raise Trap("trap")
    # 11
    if tab["elem"][i] == None:
        raise Trap("trap")
    # 12
    a = tab["elem"][i]
    # 14
    f = S["funcs"][a]
    # 15
    ftactual = f["type"]
    # 16
    if ftexpect != ftactual:
        raise Trap("trap")
    # 17
    ret = spec_invoke_function_address(config, a)


# 4.4.6 BLOCKS


def spec_enter_block(config, instrstar, L):
    logger.debug('spec_enter_block()')

    # 1
    config["control_stack"].append(L)
    # 2
    config["instrstar"] = instrstar
    config["idx"] = 0


# this is unused, just done in spec_expr() since need to check if label stack is empty
def spec_exit_block(config):
    # TODO: decide if this can be removed per the comment above
    logger.debug('spec_exit_block()')

    # 4
    L = config["control_stack"].pop()
    # 6
    config["instrstar"], config["idx"] = L["end"]


# 4.4.7 FUNCTION CALLS

# this is called by spac_call() and spec_call_indirect()
def spec_invoke_function_address(config, a=None):
    logger.debug('spec_invoke_function_address(%s)', a)

    # a is address
    S = config["S"]
    F = config["F"]
    if len(F) > 1024:
        # TODO: this is not part of spec, but this is required to pass tests.
        # Tests pass with limit 10000, maybe more
        raise Exhaustion("Function length greater than 1024")
    instrstar = config["instrstar"]
    idx = config["idx"]
    operand_stack = config["operand_stack"]
    control_stack = config["control_stack"]
    if a == None:
        a = config["instrstar"][config["idx"]][1]
    # 2
    f = S["funcs"][a]
    # 3
    t1n, t2m = f["type"]
    if "code" in f:
        # 5
        tstar = f["code"]["locals"]
        # 6
        instrstarend = f["code"]["body"]
        # 8
        valn = []
        if len(t1n) > 0:
            valn = operand_stack[-1 * len(t1n) :]
            del operand_stack[-1 * len(t1n) :]
        # 9
        val0star = []
        for t in tstar:
            if is_integer_type(t):
                val0star += [0]
            elif is_float_type(t):
                val0star += [0.0]
            else:
                raise Exception(f"Invariant: unkown type '{t}'")
        # 10 & 11
        F += [
            {
                "module": f["module"],
                "locals": valn + val0star,
                "arity": len(t2m),
                "height": len(operand_stack),
                "continuation": [instrstar, idx + 1, control_stack],
            }
        ]
        # 12
        retval = [] if not t2m else t2m[0]
        blockinstrstarendend = [["block", retval, instrstarend], ["end"]]
        config["instrstar"] = blockinstrstarendend
        config["idx"] = 0
        config["control_stack"] = []
        # TODO: confirm that 1) this code path is actually used and two that it
        # complies with the spec.  Multiple lines of commented code were
        # removed from here indicating there may be in-implemented or
        # incorrectly implemented logic
    elif "hostcode" in f:
        valn = []
        if len(t1n) > 0:
            valn = operand_stack[-1 * len(t1n) :]
            del operand_stack[-1 * len(t1n) :]
        S, ret = f["hostcode"](S, valn)

        operand_stack += ret
        config["idx"] += 1
    else:
        raise Exception("Invariant: unreachable code path")


# this is unused for now
# this is called when end of function reached without return or trap aborting it
def spec_return_from_func(config):
    logger.debug('spec_return_from_func()')

    # 1
    F = config["F"][-1]
    # 2,3,4,7 not needed since we have separate operand stack
    # 6
    config["F"].pop()
    # 8
    config["instrstar"], config["idx"], config["control_stack"] = F["continuation"]


def spec_end(config):
    logger.debug('spec_end()')

    if len(config["control_stack"]) >= 1:
        spec_exit_block(config)
    else:
        if (
            len(config["F"]) >= 1 and "continuation" in config["F"][-1]
        ):  # continuation for case of init elem or data or global
            spec_return_from_func(config)
        else:
            return "done"


# 4.4.8 EXPRESSIONS

# Map each opcode to the function(s) to invoke when it is encountered. For opcodes with two functions, the second function is called by the first function.
opcode2exec = {
    "unreachable": (spec_unreachable,),
    "nop": (spec_nop,),
    "block": (spec_block,),  # blocktype in* end
    "loop": (spec_loop,),  # blocktype in* end
    "if": (spec_if,),  # blocktype in1* else? in2* end
    "else": (spec_end,),  # in2*
    "end": (spec_end,),
    "br": (spec_br,),  # labelidx
    "br_if": (spec_br_if,),  # labelidx
    "br_table": (spec_br_table,),  # labelidx* labelidx
    "return": (spec_return,),
    "call": (spec_call,),  # funcidx
    "call_indirect": (spec_call_indirect,),  # typeidx 0x00
    "drop": (spec_drop,),
    "select": (spec_select,),
    "get_local": (spec_get_local,),  # localidx
    "set_local": (spec_set_local,),  # localidx
    "tee_local": (spec_tee_local,),  # localidx
    "get_global": (spec_get_global,),  # globalidx
    "set_global": (spec_set_global,),  # globalidx
    "i32.load": (spec_tload,),  # memarg
    "i64.load": (spec_tload,),  # memarg
    "f32.load": (spec_tload,),  # memarg
    "f64.load": (spec_tload,),  # memarg
    "i32.load8_s": (spec_tload,),  # memarg
    "i32.load8_u": (spec_tload,),  # memarg
    "i32.load16_s": (spec_tload,),  # memarg
    "i32.load16_u": (spec_tload,),  # memarg
    "i64.load8_s": (spec_tload,),  # memarg
    "i64.load8_u": (spec_tload,),  # memarg
    "i64.load16_s": (spec_tload,),  # memarg
    "i64.load16_u": (spec_tload,),  # memarg
    "i64.load32_s": (spec_tload,),  # memarg
    "i64.load32_u": (spec_tload,),  # memarg
    "i32.store": (spec_tstore,),  # memarg
    "i64.store": (spec_tstore,),  # memarg
    "f32.store": (spec_tstore,),  # memarg
    "f64.store": (spec_tstore,),  # memarg
    "i32.store8": (spec_tstore,),  # memarg
    "i32.store16": (spec_tstore,),  # memarg
    "i64.store8": (spec_tstore,),  # memarg
    "i64.store16": (spec_tstore,),  # memarg
    "i64.store32": (spec_tstore,),  # memarg
    "memory.size": (spec_memorysize,),
    "memory.grow": (spec_memorygrow,),
    "i32.const": (spec_tconst,),  # i32
    "i64.const": (spec_tconst,),  # i64
    "f32.const": (spec_tconst,),  # f32
    "f64.const": (spec_tconst,),  # f64
    "i32.eqz": (spec_ttestop, spec_ieqzN),
    "i32.eq": (spec_trelop, spec_ieqN),
    "i32.ne": (spec_trelop, spec_ineN),
    "i32.lt_s": (spec_trelop, spec_ilt_sN),
    "i32.lt_u": (spec_trelop, spec_ilt_uN),
    "i32.gt_s": (spec_trelop, spec_igt_sN),
    "i32.gt_u": (spec_trelop, spec_igt_uN),
    "i32.le_s": (spec_trelop, spec_ile_sN),
    "i32.le_u": (spec_trelop, spec_ile_uN),
    "i32.ge_s": (spec_trelop, spec_ige_sN),
    "i32.ge_u": (spec_trelop, spec_ige_uN),
    "i64.eqz": (spec_ttestop, spec_ieqzN),
    "i64.eq": (spec_trelop, spec_ieqN),
    "i64.ne": (spec_trelop, spec_ineN),
    "i64.lt_s": (spec_trelop, spec_ilt_sN),
    "i64.lt_u": (spec_trelop, spec_ilt_uN),
    "i64.gt_s": (spec_trelop, spec_igt_sN),
    "i64.gt_u": (spec_trelop, spec_igt_uN),
    "i64.le_s": (spec_trelop, spec_ile_sN),
    "i64.le_u": (spec_trelop, spec_ile_uN),
    "i64.ge_s": (spec_trelop, spec_ige_sN),
    "i64.ge_u": (spec_trelop, spec_ige_uN),
    "f32.eq": (spec_trelop, spec_feqN),
    "f32.ne": (spec_trelop, spec_fneN),
    "f32.lt": (spec_trelop, spec_fltN),
    "f32.gt": (spec_trelop, spec_fgtN),
    "f32.le": (spec_trelop, spec_fleN),
    "f32.ge": (spec_trelop, spec_fgeN),
    "f64.eq": (spec_trelop, spec_feqN),
    "f64.ne": (spec_trelop, spec_fneN),
    "f64.lt": (spec_trelop, spec_fltN),
    "f64.gt": (spec_trelop, spec_fgtN),
    "f64.le": (spec_trelop, spec_fleN),
    "f64.ge": (spec_trelop, spec_fgeN),
    "i32.clz": (spec_tunop, spec_iclzN),
    "i32.ctz": (spec_tunop, spec_ictzN),
    "i32.popcnt": (spec_tunop, spec_ipopcntN),
    "i32.add": (spec_tbinop, spec_iaddN),
    "i32.sub": (spec_tbinop, spec_isubN),
    "i32.mul": (spec_tbinop, spec_imulN),
    "i32.div_s": (spec_tbinop, spec_idiv_sN),
    "i32.div_u": (spec_tbinop, spec_idiv_uN),
    "i32.rem_s": (spec_tbinop, spec_irem_sN),
    "i32.rem_u": (spec_tbinop, spec_irem_uN),
    "i32.and": (spec_tbinop, spec_iandN),
    "i32.or": (spec_tbinop, spec_iorN),
    "i32.xor": (spec_tbinop, spec_ixorN),
    "i32.shl": (spec_tbinop, spec_ishlN),
    "i32.shr_s": (spec_tbinop, spec_ishr_sN),
    "i32.shr_u": (spec_tbinop, spec_ishr_uN),
    "i32.rotl": (spec_tbinop, spec_irotlN),
    "i32.rotr": (spec_tbinop, spec_irotrN),
    "i64.clz": (spec_tunop, spec_iclzN),
    "i64.ctz": (spec_tunop, spec_ictzN),
    "i64.popcnt": (spec_tunop, spec_ipopcntN),
    "i64.add": (spec_tbinop, spec_iaddN),
    "i64.sub": (spec_tbinop, spec_isubN),
    "i64.mul": (spec_tbinop, spec_imulN),
    "i64.div_s": (spec_tbinop, spec_idiv_sN),
    "i64.div_u": (spec_tbinop, spec_idiv_uN),
    "i64.rem_s": (spec_tbinop, spec_irem_sN),
    "i64.rem_u": (spec_tbinop, spec_irem_uN),
    "i64.and": (spec_tbinop, spec_iandN),
    "i64.or": (spec_tbinop, spec_iorN),
    "i64.xor": (spec_tbinop, spec_ixorN),
    "i64.shl": (spec_tbinop, spec_ishlN),
    "i64.shr_s": (spec_tbinop, spec_ishr_sN),
    "i64.shr_u": (spec_tbinop, spec_ishr_uN),
    "i64.rotl": (spec_tbinop, spec_irotlN),
    "i64.rotr": (spec_tbinop, spec_irotrN),
    "f32.abs": (spec_tunop, spec_fabsN),
    "f32.neg": (spec_tunop, spec_fnegN),
    "f32.ceil": (spec_tunop, spec_fceilN),
    "f32.floor": (spec_tunop, spec_ffloorN),
    "f32.trunc": (spec_tunop, spec_ftruncN),
    "f32.nearest": (spec_tunop, spec_fnearestN),
    "f32.sqrt": (spec_tunop, spec_fsqrtN),
    "f32.add": (spec_tbinop, spec_faddN),
    "f32.sub": (spec_tbinop, spec_fsubN),
    "f32.mul": (spec_tbinop, spec_fmulN),
    "f32.div": (spec_tbinop, spec_fdivN),
    "f32.min": (spec_tbinop, spec_fminN),
    "f32.max": (spec_tbinop, spec_fmaxN),
    "f32.copysign": (spec_tbinop, spec_fcopysignN),
    "f64.abs": (spec_tunop, spec_fabsN),
    "f64.neg": (spec_tunop, spec_fnegN),
    "f64.ceil": (spec_tunop, spec_fceilN),
    "f64.floor": (spec_tunop, spec_ffloorN),
    "f64.trunc": (spec_tunop, spec_ftruncN),
    "f64.nearest": (spec_tunop, spec_fnearestN),
    "f64.sqrt": (spec_tunop, spec_fsqrtN),
    "f64.add": (spec_tbinop, spec_faddN),
    "f64.sub": (spec_tbinop, spec_fsubN),
    "f64.mul": (spec_tbinop, spec_fmulN),
    "f64.div": (spec_tbinop, spec_fdivN),
    "f64.min": (spec_tbinop, spec_fminN),
    "f64.max": (spec_tbinop, spec_fmaxN),
    "f64.copysign": (spec_tbinop, spec_fcopysignN),
    "i32.wrap/i64": (spec_t2cvtopt1, spec_wrapMN),
    "i32.trunc_s/f32": (spec_t2cvtopt1, spec_trunc_sMN),
    "i32.trunc_u/f32": (spec_t2cvtopt1, spec_trunc_uMN),
    "i32.trunc_s/f64": (spec_t2cvtopt1, spec_trunc_sMN),
    "i32.trunc_u/f64": (spec_t2cvtopt1, spec_trunc_uMN),
    "i64.extend_s/i32": (spec_t2cvtopt1, spec_extend_sMN),
    "i64.extend_u/i32": (spec_t2cvtopt1, spec_extend_uMN),
    "i64.trunc_s/f32": (spec_t2cvtopt1, spec_trunc_sMN),
    "i64.trunc_u/f32": (spec_t2cvtopt1, spec_trunc_uMN),
    "i64.trunc_s/f64": (spec_t2cvtopt1, spec_trunc_sMN),
    "i64.trunc_u/f64": (spec_t2cvtopt1, spec_trunc_uMN),
    "f32.convert_s/i32": (spec_t2cvtopt1, spec_convert_sMN),
    "f32.convert_u/i32": (spec_t2cvtopt1, spec_convert_uMN),
    "f32.convert_s/i64": (spec_t2cvtopt1, spec_convert_sMN),
    "f32.convert_u/i64": (spec_t2cvtopt1, spec_convert_uMN),
    "f32.demote/f64": (spec_t2cvtopt1, spec_demoteMN),
    "f64.convert_s/i32": (spec_t2cvtopt1, spec_convert_sMN),
    "f64.convert_u/i32": (spec_t2cvtopt1, spec_convert_uMN),
    "f64.convert_s/i64": (spec_t2cvtopt1, spec_convert_sMN),
    "f64.convert_u/i64": (spec_t2cvtopt1, spec_convert_uMN),
    "f64.promote/f32": (spec_t2cvtopt1, spec_promoteMN),
    "i32.reinterpret/f32": (spec_t2cvtopt1, spec_reinterprett1t2),
    "i64.reinterpret/f64": (spec_t2cvtopt1, spec_reinterprett1t2),
    "f32.reinterpret/i32": (spec_t2cvtopt1, spec_reinterprett1t2),
    "f64.reinterpret/i64": (spec_t2cvtopt1, spec_reinterprett1t2),
    "invoke": (spec_invoke_function_address,),
}


# this is the main loop over instr* end
# this is not in the spec
def instrstarend_loop(config):
    logger.debug('instrstarend_loop()')

    # TODO: try to refactor to make this loop have a defined exit condition.
    while True:
        instr = config["instrstar"][config["idx"]][
            0
        ]  # idx<len(instrs) since instrstar[-1]=="end" which changes instrstar
        ret = opcode2exec[instr][0](config)
        if ret:
            return ret, config["operand_stack"]  # eg "done"


# this executes instr* end. This deviates from the spec.
def spec_expr(config):
    logger.debug('spec_expr()')

    config["idx"] = 0
    while 1:
        instr = config["instrstar"][config["idx"]][
            0
        ]  # idx<len(instrs) since instrstar[-1]=="end" which changes instrstar
        ret = opcode2exec[instr][0](config)

        if ret:
            return config["operand_stack"]
        else:
            # TODO: log at DEBUG2
            logger.debug('operand_stack: %s', config["operand_stack"])
            # TODO: log at DEBUG3
            logger.debug('control_stack: %s', config["control_stack"])


#############
# 4.5 MODULES
#############

# 4.5.1 EXTERNAL TYPING

def spec_external_typing(S, externval):
    logger.debug('spec_external_typing(%s)', externval)

    if "func" == externval[0]:
        a = externval[1]
        if len(S["funcs"]) < a:
            raise Unlinkable("unlinkable")
        funcinst = S["funcs"][a]
        return ["func", funcinst["type"]]
    elif "table" == externval[0]:
        a = externval[1]
        if len(S["tables"]) < a:
            raise Unlinkable("unlinkable")
        tableinst = S["tables"][a]
        return [
            "table",
            [{"min": len(tableinst["elem"]), "max": tableinst["max"]}, "anyfunc"],
        ]
    elif "mem" == externval[0]:
        a = externval[1]
        if len(S["mems"]) < a:
            raise Unlinkable("unlinkable")
        meminst = S["mems"][a]
        return [
            "mem",
            {
                "min": len(meminst["data"]) // constants.PAGE_SIZE_64K,
                "max": meminst["max"],
            },
        ]
    elif "global" == externval[0]:
        a = externval[1]
        if len(S["globals"]) < a:
            raise Unlinkable("unlinkable")
        globalinst = S["globals"][a]
        return ["global", [globalinst["mut"], globalinst["value"][0][:3]]]
    else:
        raise Unlinkable("unlinkable")


# 4.5.2 IMPORT MATCHING


def spec_externtype_matching_limits(limits1, limits2):
    logger.debug('spec_externtype_matching_limits(%s, %s)', limits1, limits2)

    n1 = limits1["min"]
    m1 = limits1["max"]
    n2 = limits2["min"]
    m2 = limits2["max"]

    if n1 < n2:
        raise Unlinkable("unlinkable")
    elif m2 == None or (m1 != None and m2 != None and m1 <= m2):
        return "<="
    else:
        raise Unlinkable("unlinkable")


def spec_externtype_matching(externtype1, externtype2):
    logger.debug('spec_externtype_matching(%s, %s)', externtype1, externtype2)

    if externtype1[0] != externtype2[0]:
        raise Unlinkable(f"Mismatch in extern types: {externtype1[0]} != {externtype2[0]}")
    elif "func" == externtype1[0] and "func" == externtype2[0]:
        if externtype1[1] == externtype2[1]:
            return "<="
        else:
            raise Unlinkable(f"Function extern type mismatch: {externtype1[1]} != {externtype2[1]}")
    elif "table" == externtype1[0] and "table" == externtype2[0]:
        limits1 = externtype1[1][0]
        limits2 = externtype2[1][0]
        spec_externtype_matching_limits(limits1, limits2)
        elemtype1 = externtype1[1][1]
        elemtype2 = externtype2[1][1]
        if elemtype1 == elemtype2:
            return "<="
        else:
            raise Unlinkable(f"Table element type mismatch: {elemtype1} != {elemtype2}")
    elif "mem" == externtype1[0] and "mem" == externtype2[0]:
        limits1 = externtype1[1]
        limits2 = externtype2[1]
        if spec_externtype_matching_limits(limits1, limits2) == "<=":
            return "<="
        else:
            # TODO: This code path doesn't appear to be excercised and it
            # likely isn't an invariant.
            raise Exception("Invariant")
    elif "global" == externtype1[0] and "global" == externtype2[0]:
        if externtype1[1] == externtype2[1]:
            return "<="
        else:
            raise Unlinkable(f"Globals extern type mismatch: {externtype1[1]} != {externtype2[1]}")
    else:
        raise Unlinkable(f"Unknown extern type: {externtype1[0]}")


# 4.5.3 ALLOCATION


def spec_allocfunc(S, func, moduleinst):
    logger.debug('spec_allocfunc()')

    funcaddr = len(S["funcs"])
    functype = moduleinst["types"][func["type"]]
    funcinst = {"type": functype, "module": moduleinst, "code": func}
    S["funcs"].append(funcinst)
    return S, funcaddr


def spec_allochostfunc(S, functype, hostfunc):
    logger.debug('spec_allochostfunc()')

    funcaddr = len(S["funcs"])
    funcinst = {"type": functype, "hostcode": hostfunc}
    S["funcs"].append(funcinst)
    return S, funcaddr


def spec_alloctable(S, tabletype):
    logger.debug('spec_alloctable()')

    min_ = tabletype[0]["min"]
    max_ = tabletype[0]["max"]
    tableaddr = len(S["tables"])
    tableinst = {"elem": [None for i in range(min_)], "max": max_}
    S["tables"].append(tableinst)
    return S, tableaddr


def spec_allocmem(S, memtype):
    logger.debug('spec_allocmem()')

    min_ = memtype["min"]
    max_ = memtype["max"]
    memaddr = len(S["mems"])
    meminst = {
        "data": bytearray(min_ * constants.PAGE_SIZE_64K),
        "max": max_,
    }
    S["mems"].append(meminst)
    return S, memaddr


def spec_allocglobal(S, globaltype, val):
    logger.debug('spec_allocglobal()')

    mut = globaltype[0]
    valtype = globaltype[1]
    globaladdr = len(S["globals"])
    globalinst = {"value": [valtype + ".const", val], "mut": mut}
    S["globals"].append(globalinst)
    return S, globaladdr


def spec_growtable(tableinst, n):
    logger.debug('spec_growtable()')

    len_ = n + len(tableinst["elem"])

    if len_ >= constants.UINT32_CEIL:
        return "fail"
    elif tablinst["max"] != None and tableinst["max"] < len_:
        return "fail"  # TODO: what does fail mean? raise Exception("trap")
    else:
        tableinst["elem"] += [None for i in range(n)]

    return tableinst


def spec_growmem(meminst, n):
    logger.debug('spec_growmem()')

    if len(meminst["data"]) % constants.PAGE_SIZE_64K != 0:
        raise Exception("TODO: more appropriate exception type")

    len_ = n + len(meminst["data"]) // constants.PAGE_SIZE_64K
    if len_ >= constants.UINT16_CEIL:
        return "fail"
    elif meminst["max"] != None and meminst["max"] < len_:
        return "fail"
        # TODO: what does fail mean? raise Exception("trap")

    meminst["data"] += bytearray(
        n * constants.PAGE_SIZE_64K
    )  # each page created with bytearray(65536) which is 0s


def spec_allocmodule(S, module, externvalimstar, valstar):
    logger.debug('spec_allocmodule()')

    moduleinst = {
        "types": module["types"],
        "funcaddrs": None,
        "tableaddrs": None,
        "memaddrs": None,
        "globaladdrs": None,
        "exports": None,
    }
    funcaddrstar = [spec_allocfunc(S, func, moduleinst)[1] for func in module["funcs"]]
    tableaddrstar = [spec_alloctable(S, table["type"])[1] for table in module["tables"]]
    memaddrstar = [spec_allocmem(S, mem["type"])[1] for mem in module["mems"]]
    globaladdrstar = [
        spec_allocglobal(S, global_["type"], valstar[idx])[1]
        for idx, global_ in enumerate(module["globals"])
    ]
    funcaddrmodstar = spec_funcs(externvalimstar) + funcaddrstar
    tableaddrmodstar = spec_tables(externvalimstar) + tableaddrstar
    memaddrmodstar = spec_mems(externvalimstar) + memaddrstar
    globaladdrmodstar = spec_globals(externvalimstar) + globaladdrstar
    exportinststar = []
    for exporti in module["exports"]:
        if exporti["desc"][0] == "func":
            x = exporti["desc"][1]
            externvali = ["func", funcaddrmodstar[x]]
        elif exporti["desc"][0] == "table":
            x = exporti["desc"][1]
            externvali = ["table", tableaddrmodstar[x]]
        elif exporti["desc"][0] == "mem":
            x = exporti["desc"][1]
            externvali = ["mem", memaddrmodstar[x]]
        elif exporti["desc"][0] == "global":
            x = exporti["desc"][1]
            externvali = ["global", globaladdrmodstar[x]]
        else:
            raise Exception("Invariant: TODO: bettermessage")

        exportinststar += [{"name": exporti["name"], "value": externvali}]
    moduleinst["funcaddrs"] = funcaddrmodstar
    moduleinst["tableaddrs"] = tableaddrmodstar
    moduleinst["memaddrs"] = memaddrmodstar
    moduleinst["globaladdrs"] = globaladdrmodstar
    moduleinst["exports"] = exportinststar
    return S, moduleinst


def spec_instantiate(S, module, externvaln):
    logger.debug('spec_instantiate()')

    # 1
    # 2
    ret = spec_validate_module(module)
    externtypeimn, externtypeexstar = ret
    # 3
    if len(module["imports"]) != len(externvaln):
        raise Unlinkable("unlinkable")
    # 4
    for i in range(len(externvaln)):
        externtypei = spec_external_typing(S, externvaln[i])
        spec_externtype_matching(externtypei, externtypeimn[i])
    # 5
    valstar = []
    moduleinstim = {
        "globaladdrs": [
            externval[1] for externval in externvaln if "global" == externval[0]
        ]
    }
    Fim = {"module": moduleinstim, "locals": [], "arity": 1, "height": 0}
    framestack = []
    framestack += [Fim]
    for globali in module["globals"]:
        config = {
            "S": S,
            "F": framestack,
            "instrstar": globali["init"],
            "idx": 0,
            "operand_stack": [],
            "control_stack": [],
        }
        ret = spec_expr(config)[0]
        valstar += [ret]
    framestack.pop()
    # 6
    S, moduleinst = spec_allocmodule(S, module, externvaln, valstar)
    # 7
    F = {"module": moduleinst, "locals": []}
    # 8
    framestack += [F]
    # 9
    tableinst = []
    eo = []
    for elemi in module["elem"]:
        config = {
            "S": S,
            "F": framestack,
            "instrstar": elemi["offset"],
            "idx": 0,
            "operand_stack": [],
            "control_stack": [],
        }
        eovali = spec_expr(config)[0]
        eoi = eovali
        eo += [eoi]
        tableidxi = elemi["table"]
        tableaddri = moduleinst["tableaddrs"][tableidxi]
        tableinsti = S["tables"][tableaddri]
        tableinst += [tableinsti]
        eendi = eoi + len(elemi["init"])
        if eendi > len(tableinsti["elem"]):
            raise Unlinkable("unlinkable")
    # 10
    meminst = []
    do = []
    for datai in module["data"]:
        config = {
            "S": S,
            "F": framestack,
            "instrstar": datai["offset"],
            "idx": 0,
            "operand_stack": [],
            "control_stack": [],
        }
        dovali = spec_expr(config)[0]
        doi = dovali
        do += [doi]
        memidxi = datai["data"]
        memaddri = moduleinst["memaddrs"][memidxi]
        meminsti = S["mems"][memaddri]
        meminst += [meminsti]
        dendi = doi + len(datai["init"])
        if dendi > len(meminsti["data"]):
            raise Unlinkable("unlinkable")
    # 11
    # 12
    framestack.pop()
    # 13
    for i, elemi in enumerate(module["elem"]):
        for j, funcidxij in enumerate(elemi["init"]):
            funcaddrij = moduleinst["funcaddrs"][funcidxij]
            tableinst[i]["elem"][eo[i] + j] = funcaddrij
    # 14
    for i, datai in enumerate(module["data"]):
        for j, bij in enumerate(datai["init"]):
            meminst[i]["data"][do[i] + j] = bij
    # 15
    if module["start"]:
        funcaddr = moduleinst["funcaddrs"][module["start"]["func"]]
        ret = spec_invoke(S, funcaddr, [])
    else:
        ret = None

    return S, F, ret


# 4.5.5 INVOCATION

# valn looks like [["i32.const",3],["i32.const",199], ...]
def spec_invoke(S, funcaddr, valn):
    logger.debug('spec_invoke()')

    # 1
    if len(S["funcs"]) < funcaddr or funcaddr < 0:
        raise Exception("bad address")
    # 2
    funcinst = S["funcs"][funcaddr]
    # 5
    t1n, t2m = funcinst["type"]
    # 4
    if len(valn) != len(t1n):
        raise Exception("wrong number of arguments")
    # 5
    for ti, vali in zip(t1n, valn):
        if vali[0][:3] != ti:
            raise Exception("argument type mismatch")
    # 6
    operand_stack = []
    for ti, vali in zip(t1n, valn):
        arg = vali[1]
        if type(arg) == str:
            if is_integer_type(ti):
                arg = int(arg)
            elif is_float_type(ti):
                arg = float(arg)
            else:
                raise Exception(f"Invariant: unknown type '{t}'")

        operand_stack += [arg]
    # 7
    valresm = None
    if "code" in funcinst:
        # config = {"S":S,"F":[],"instrstar":funcinst["code"]["body"],"idx":0,"operand_stack":operand_stack,"control_stack":[]}  #TODO: toggle these back when uncomment main loop execution
        # valresm = spec_invoke_function_address(config,funcaddr)  #TODO: toggle these back when uncomment main loop execution
        config = {
            "S": S,
            "F": [],
            "instrstar": [["invoke", funcaddr], ["end", None]],
            "idx": 0,
            "operand_stack": operand_stack,
            "control_stack": [],
        }
        valresm = spec_expr(config)  # instrstarend_loop(config)
        # moved this here from bottom
        return valresm
    elif "hostcode" in funcinst:
        S, valresm = funcinst["hostcode"](S, operand_stack)
        # moved this here from bottom
        return valresm
    else:
        raise Exception("")
    # return valresm  #TODO: toggle these back when uncomment main loop execution


###################
###################
# 5 BINARY FORMAT #
###################
###################

# Chapter 5 defines a binary syntax over the abstract syntax. The implementation is a recursive-descent parser which takes a `.wasm` file and builds an abstract syntax tree out of nested Python lists and dicts. Also implemented are inverses (up to a canonical form) which write an abstract syntax tree back to a `.wasm` file.

# key-value pairs of binary opcodes and their text reperesentation
opcodes_binary2text = {
    0x00: "unreachable",
    0x01: "nop",
    0x02: "block",  # blocktype in* end		# begin block
    0x03: "loop",  # blocktype in* end		# begin block
    0x04: "if",  # blocktype in1* else? end	# begin block
    0x05: "else",  # in2*				# end block & begin block
    0x0B: "end",  # end block
    0x0C: "br",  # labelidx			# branch
    0x0D: "br_if",  # labelidx			# branch
    0x0E: "br_table",  # labelidx* labelidx		# branch
    0x0F: "return",  # end outermost block
    0x10: "call",  # funcidx			# branch
    0x11: "call_indirect",  # typeidx 0x00			# branch
    0x1A: "drop",
    0x1B: "select",
    0x20: "get_local",  # localidx
    0x21: "set_local",  # localidx
    0x22: "tee_local",  # localidx
    0x23: "get_global",  # globalidx
    0x24: "set_global",  # globalidx
    0x28: "i32.load",  # memarg
    0x29: "i64.load",  # memarg
    0x2A: "f32.load",  # memarg
    0x2B: "f64.load",  # memarg
    0x2C: "i32.load8_s",  # memarg
    0x2D: "i32.load8_u",  # memarg
    0x2E: "i32.load16_s",  # memarg
    0x2F: "i32.load16_u",  # memarg
    0x30: "i64.load8_s",  # memarg
    0x31: "i64.load8_u",  # memarg
    0x32: "i64.load16_s",  # memarg
    0x33: "i64.load16_u",  # memarg
    0x34: "i64.load32_s",  # memarg
    0x35: "i64.load32_u",  # memarg
    0x36: "i32.store",  # memarg
    0x37: "i64.store",  # memarg
    0x38: "f32.store",  # memarg
    0x39: "f64.store",  # memarg
    0x3A: "i32.store8",  # memarg
    0x3B: "i32.store16",  # memarg
    0x3C: "i64.store8",  # memarg
    0x3D: "i64.store16",  # memarg
    0x3E: "i64.store32",  # memarg
    0x3F: "memory.size",
    0x40: "memory.grow",
    0x41: "i32.const",  # i32
    0x42: "i64.const",  # i64
    0x43: "f32.const",  # f32
    0x44: "f64.const",  # f64
    0x45: "i32.eqz",
    0x46: "i32.eq",
    0x47: "i32.ne",
    0x48: "i32.lt_s",
    0x49: "i32.lt_u",
    0x4A: "i32.gt_s",
    0x4B: "i32.gt_u",
    0x4C: "i32.le_s",
    0x4D: "i32.le_u",
    0x4E: "i32.ge_s",
    0x4F: "i32.ge_u",
    0x50: "i64.eqz",
    0x51: "i64.eq",
    0x52: "i64.ne",
    0x53: "i64.lt_s",
    0x54: "i64.lt_u",
    0x55: "i64.gt_s",
    0x56: "i64.gt_u",
    0x57: "i64.le_s",
    0x58: "i64.le_u",
    0x59: "i64.ge_s",
    0x5A: "i64.ge_u",
    0x5B: "f32.eq",
    0x5C: "f32.ne",
    0x5D: "f32.lt",
    0x5E: "f32.gt",
    0x5F: "f32.le",
    0x60: "f32.ge",
    0x61: "f64.eq",
    0x62: "f64.ne",
    0x63: "f64.lt",
    0x64: "f64.gt",
    0x65: "f64.le",
    0x66: "f64.ge",
    0x67: "i32.clz",
    0x68: "i32.ctz",
    0x69: "i32.popcnt",
    0x6A: "i32.add",
    0x6B: "i32.sub",
    0x6C: "i32.mul",
    0x6D: "i32.div_s",
    0x6E: "i32.div_u",
    0x6F: "i32.rem_s",
    0x70: "i32.rem_u",
    0x71: "i32.and",
    0x72: "i32.or",
    0x73: "i32.xor",
    0x74: "i32.shl",
    0x75: "i32.shr_s",
    0x76: "i32.shr_u",
    0x77: "i32.rotl",
    0x78: "i32.rotr",
    0x79: "i64.clz",
    0x7A: "i64.ctz",
    0x7B: "i64.popcnt",
    0x7C: "i64.add",
    0x7D: "i64.sub",
    0x7E: "i64.mul",
    0x7F: "i64.div_s",
    0x80: "i64.div_u",
    0x81: "i64.rem_s",
    0x82: "i64.rem_u",
    0x83: "i64.and",
    0x84: "i64.or",
    0x85: "i64.xor",
    0x86: "i64.shl",
    0x87: "i64.shr_s",
    0x88: "i64.shr_u",
    0x89: "i64.rotl",
    0x8A: "i64.rotr",
    0x8B: "f32.abs",
    0x8C: "f32.neg",
    0x8D: "f32.ceil",
    0x8E: "f32.floor",
    0x8F: "f32.trunc",
    0x90: "f32.nearest",
    0x91: "f32.sqrt",
    0x92: "f32.add",
    0x93: "f32.sub",
    0x94: "f32.mul",
    0x95: "f32.div",
    0x96: "f32.min",
    0x97: "f32.max",
    0x98: "f32.copysign",
    0x99: "f64.abs",
    0x9A: "f64.neg",
    0x9B: "f64.ceil",
    0x9C: "f64.floor",
    0x9D: "f64.trunc",
    0x9E: "f64.nearest",
    0x9F: "f64.sqrt",
    0xA0: "f64.add",
    0xA1: "f64.sub",
    0xA2: "f64.mul",
    0xA3: "f64.div",
    0xA4: "f64.min",
    0xA5: "f64.max",
    0xA6: "f64.copysign",
    0xA7: "i32.wrap/i64",
    0xA8: "i32.trunc_s/f32",
    0xA9: "i32.trunc_u/f32",
    0xAA: "i32.trunc_s/f64",
    0xAB: "i32.trunc_u/f64",
    0xAC: "i64.extend_s/i32",
    0xAD: "i64.extend_u/i32",
    0xAE: "i64.trunc_s/f32",
    0xAF: "i64.trunc_u/f32",
    0xB0: "i64.trunc_s/f64",
    0xB1: "i64.trunc_u/f64",
    0xB2: "f32.convert_s/i32",
    0xB3: "f32.convert_u/i32",
    0xB4: "f32.convert_s/i64",
    0xB5: "f32.convert_u/i64",
    0xB6: "f32.demote/f64",
    0xB7: "f64.convert_s/i32",
    0xB8: "f64.convert_u/i32",
    0xB9: "f64.convert_s/i64",
    0xBA: "f64.convert_u/i64",
    0xBB: "f64.promote/f32",
    0xBC: "i32.reinterpret/f32",
    0xBD: "i64.reinterpret/f64",
    0xBE: "f32.reinterpret/i32",
    0xBF: "f64.reinterpret/i64",
}

# key-value pairs of text opcodes and their binary reperesentation
opcodes_text2binary = {}
for opcode in opcodes_binary2text:
    opcodes_text2binary[opcodes_binary2text[opcode]] = opcode


# 5.1.3 VECTORS


def spec_binary_vec(raw, idx, B):
    logger.debug('spec_binary_vec(%s)', idx)

    idx, num = spec_binary_uN(raw, idx, 32)
    xn = []
    for i in range(num):
        idx, x = B(raw, idx)
        xn += [x]
    return idx, xn


def spec_binary_vec_inv(mynode, myfunc):
    n_bytes = spec_binary_uN_inv(len(mynode), 32)
    xn_bytes = bytearray()
    for x in mynode:
        xn_bytes += myfunc(x)
    return n_bytes + xn_bytes


############
# 5.2 VALUES
############

# 5.2.1 BYTES


def spec_binary_byte(raw, idx):
    if len(raw) <= idx:
        raise MalformedModule("malformed")
    return idx + 1, raw[idx]


def spec_binary_byte_inv(node):
    return bytearray([node])


# 5.2.2 INTEGERS

# unsigned
def spec_binary_uN(raw, idx, N):
    logger.debug('spec_binary_uN(%s, %s)', idx, N)

    idx, n = spec_binary_byte(raw, idx)
    if n < 2 ** 7 and n < 2 ** N:
        return idx, n
    elif n >= 2 ** 7 and N > 7:
        idx, m = spec_binary_uN(raw, idx, N - 7)
        return idx, (2 ** 7) * m + (n - 2 ** 7)
    else:
        raise MalformedModule("malformed")


def spec_binary_uN_inv(k, N):
    logger.debug('spec_binary_uN_inv(%s, %s)', k, N)

    if k < 2 ** 7 and k < 2 ** N:
        return bytearray([k])
    elif k >= 2 ** 7 and N > 7:
        return bytearray([k % (2 ** 7) + 2 ** 7]) + spec_binary_uN_inv(
            k // (2 ** 7), N - 7
        )
    else:
        raise MalformedModule("malformed")


# signed
def spec_binary_sN(raw, idx, N):
    n = int(raw[idx])
    idx += 1
    if n < 2 ** 6 and n < 2 ** (N - 1):
        return idx, n
    elif 2 ** 6 <= n < 2 ** 7 and n >= 2 ** 7 - 2 ** (N - 1):
        return idx, n - 2 ** 7
    elif n >= 2 ** 7 and N > 7:
        idx, m = spec_binary_sN(raw, idx, N - 7)
        return idx, 2 ** 7 * m + (n - 2 ** 7)
    else:
        raise MalformedModule("malformed")


def spec_binary_sN_inv(k, N):
    if 0 <= k < 2 ** 6 and k < 2 ** N:
        return bytearray([k])
    elif 2 ** 6 <= k + 2 ** 7 < 2 ** 7:  # and k+2**7>=2**7-2**(N-1):
        return bytearray([k + 2 ** 7])
    elif (k >= 2 ** 6 or k < 2 ** 6) and N > 7:  # (k<0 and k+2**7>=2**6)) and N>7:
        return bytearray([k % (2 ** 7) + 2 ** 7]) + spec_binary_sN_inv(
            (k // (2 ** 7)), N - 7
        )
    else:
        raise MalformedModule("malformed")


# uninterpretted integers
def spec_binary_iN(raw, idx, N):
    idx, n = spec_binary_sN(raw, idx, N)
    i = spec_signediN_inv(N, n)
    return idx, i


def spec_binary_iN_inv(i, N):
    return spec_binary_sN_inv(spec_signediN(N, i), N)


# 5.2.3 FLOATING-POINT

# fN::= b*:byte^{N/8} => bytes_{fN}^{-1}(b*)
def spec_binary_fN(raw, idx, N):
    bstar = bytearray([])
    for i in range(N // 8):
        bstar += bytearray([raw[idx]])
        idx += 1
    return idx, spec_bytest_inv(get_float_type(N), bstar)  # bytearray(bstar)


def spec_binary_fN_inv(node, N):
    return spec_bytest(get_float_type(N), node)


# 5.2.4 NAMES

# name as UTF-8 codepoints
def spec_binary_name(raw, idx):
    logger.debug('spec_binary_name()')
    idx, bstar = spec_binary_vec(raw, idx, spec_binary_byte)

    try:
        nametxt = bytearray(bstar).decode()
    except UnicodeDecodeError as err:
        raise MalformedModule from err

    return idx, nametxt

    # TODO: decide fate of this code
    # rest is unused, for finding inverse of utf8(name)=b*, keep since want to correct spec doc
    bstaridx = 0
    lenbstar = len(bstar)
    name = []
    while bstaridx < lenbstar:
        if bstaridx >= len(bstar):
            raise MalformedModule("malformed")
        b1 = bstar[bstaridx]
        bstaridx += 1
        if b1 < 0x80:
            name += [b1]
            continue
        if bstaridx >= len(bstar):
            raise MalformedModule("malformed")
        b2 = bstar[bstaridx]
        if b2 >> 6 != 0b01:
            raise MalformedModule("malformed")
        bstaridx += 1
        c = (2 ** 6) * (b1 - 0xC0) + (b2 - 0x80)
        # c_check = 2**6*(b1-192) + (b2-128)
        if 0x80 <= c < 0x800:
            name += [c]
            continue
        if bstaridx >= len(bstar):
            raise MalformedModule("malformed")
        b3 = bstar[bstaridx]
        if b2 >> 5 != 0b011:
            raise MalformedModule("malformed")
        bstaridx += 1
        c = (constants.UINT12_CEIL) * (b1 - 0xE0) + (2 ** 6) * (b2 - 0x80) + (b3 - 0x80)
        if 0x800 <= c < 0x10000 and (b2 >> 6 == 0b01):
            name += [c]
            continue
        if bstaridx >= len(bstar):
            raise MalformedModule("malformed")
        b4 = bstar[bstaridx]
        if b2 >> 4 != 0b0111:
            raise MalformedModule("malformed")
        bstaridx += 1
        c = (
            constants.UINT18_CEIL * (b1 - 0xF0)
            + constants.UINT12_CEIL * (b2 - 0x80)
            + constants.UINT6_CEIL * (b3 - 0x80)
            + (b4 - 0x80)
        )
        if 0x10000 <= c < 0x110000:
            name += [c]
        else:
            raise MalformedModule("malformed")
    # convert each codepoint to utf8 character
    nametxt = ""
    for c in name:
        nametxt += chr(c)
    return idx, nametxt


def spec_binary_name_inv(chars):
    name_bytes = bytearray()
    for c in chars:
        c = ord(c)
        if c < 0x80:
            name_bytes += bytes([c])
        elif 0x80 <= c < 0x800:
            name_bytes += bytes([(c >> 6) + 0xC0, (c & 0b111111) + 0x80])
        elif 0x800 <= c < 0x10000:
            name_bytes += bytes(
                [(c >> 12) + 0xE0, ((c >> 6) & 0b111111) + 0x80, (c & 0b111111) + 0x80]
            )
        elif 0x10000 <= c < 0x110000:
            name_bytes += bytes(
                [
                    (c >> 18) + 0xF0,
                    ((c >> 12) & 0b111111) + 0x80,
                    ((c >> 6) & 0b111111) + 0x80,
                    (c & 0b111111) + 0x80,
                ]
            )
        else:
            # TODO: return value checking cleanup
            return None  # error
    return bytearray([len(name_bytes)]) + name_bytes


###########
# 5.3 TYPES
###########

# 5.3.1 VALUE TYPES

valtype2bin = {constants.INT32: 0x7F, constants.INT64: 0x7E, constants.FLOAT32: 0x7D, constants.FLOAT64: 0x7C}
bin2valtype = {val: key for key, val in valtype2bin.items()}


def spec_binary_valtype(raw, idx):
    if idx >= len(raw):
        raise MalformedModule("malformed")
    elif raw[idx] in bin2valtype:
        return idx + 1, bin2valtype[raw[idx]]
    else:
        raise MalformedModule("malformed")


def spec_binary_valtype_inv(node):
    logger.debug("spec_binary_valtype_inv(%s)", node)

    if node in valtype2bin:
        return bytearray([valtype2bin[node]])
    else:
        return bytearray([])  # error


# 5.3.2 RESULT TYPES


def spec_binary_blocktype(raw, idx):
    if raw[idx] == 0x40:
        return idx + 1, []
    idx, t = spec_binary_valtype(raw, idx)
    return idx, t


def spec_binary_blocktype_inv(node):
    logger.debug("spec_binary_blocktype_inv(%s)", node)

    if node == []:
        return bytearray([0x40])
    else:
        return spec_binary_valtype_inv(node)


# 5.3.3 FUNCTION TYPES


def spec_binary_functype(raw, idx):
    if raw[idx] != 0x60:
        raise MalformedModule("malformed")
    idx += 1
    idx, t1star = spec_binary_vec(raw, idx, spec_binary_valtype)
    idx, t2star = spec_binary_vec(raw, idx, spec_binary_valtype)
    return idx, [t1star, t2star]


def spec_binary_functype_inv(node):
    return (
        bytearray([0x60])
        + spec_binary_vec_inv(node[0], spec_binary_valtype_inv)
        + spec_binary_vec_inv(node[1], spec_binary_valtype_inv)
    )


# 5.3.4 LIMITS


def spec_binary_limits(raw, idx):
    if raw[idx] == 0x00:
        idx, n = spec_binary_uN(raw, idx + 1, 32)
        return idx, {"min": n, "max": None}
    elif raw[idx] == 0x01:
        idx, n = spec_binary_uN(raw, idx + 1, 32)
        idx, m = spec_binary_uN(raw, idx, 32)
        return idx, {"min": n, "max": m}
    else:
        return idx, None  # error


def spec_binary_limits_inv(node):
    if node["max"] == None:
        return bytearray([0x00]) + spec_binary_uN_inv(node["min"], 32)
    else:
        return (
            bytearray([0x01])
            + spec_binary_uN_inv(node["min"], 32)
            + spec_binary_uN_inv(node["max"], 32)
        )


# 5.3.5 MEMORY TYPES


def spec_binary_memtype(raw, idx):
    return spec_binary_limits(raw, idx)


def spec_binary_memtype_inv(node):
    return spec_binary_limits_inv(node)


# 5.3.6 TABLE TYPES


def spec_binary_tabletype(raw, idx):
    idx, et = spec_binary_elemtype(raw, idx)
    idx, lim = spec_binary_limits(raw, idx)
    return idx, [lim, et]


def spec_binary_elemtype(raw, idx):
    if raw[idx] == 0x70:
        return idx + 1, "anyfunc"
    else:
        raise MalformedModule("malformed")


def spec_binary_tabletype_inv(node):
    return spec_binary_elemtype_inv(node[1]) + spec_binary_limits_inv(node[0])


def spec_binary_elemtype_inv(node):
    return bytearray([0x70])


# 5.3.7 GLOBAL TYPES


def spec_binary_globaltype(raw, idx):
    idx, t = spec_binary_valtype(raw, idx)
    idx, m = spec_binary_mut(raw, idx)
    return idx, [m, t]


def spec_binary_mut(raw, idx):
    if raw[idx] == 0x00:
        return idx + 1, "const"
    elif raw[idx] == 0x01:
        return idx + 1, "var"
    else:
        raise MalformedModule("malformed")


def spec_binary_globaltype_inv(node):
    return spec_binary_valtype_inv(node[1]) + spec_binary_mut_inv(node[0])


def spec_binary_mut_inv(node):
    if node == "const":
        return bytearray([0x00])
    elif node == "var":
        return bytearray([0x01])
    else:
        return bytearray([])


##################
# 5.4 INSTRUCTIONS
##################

# 5.4.1-5 VARIOUS INSTRUCTIONS


def spec_binary_memarg(raw, idx):
    idx, a = spec_binary_uN(raw, idx, 32)
    idx, o = spec_binary_uN(raw, idx, 32)
    return idx, {"align": a, "offset": o}


def spec_binary_memarg_inv(node):
    return spec_binary_uN_inv(node["align"], 32) + spec_binary_uN_inv(
        node["offset"], 32
    )


def spec_binary_instr(raw, idx):
    if raw[idx] not in opcodes_binary2text:
        return idx, None  # error
    instr_binary = raw[idx]
    instr_text = opcodes_binary2text[instr_binary]
    idx += 1
    if instr_text in {"block", "loop", "if"}:  # block, loop, if
        idx, rt = spec_binary_blocktype(raw, idx)
        instar = []
        if instr_text == "if":
            instar2 = []
            # TODO: open ended loop
            while raw[idx] not in {0x05, 0x0B}:
                idx, ins = spec_binary_instr(raw, idx)
                instar += [ins]
            if raw[idx] == 0x05:  # if with else
                idx += 1
                # TODO: open ended loop
                while raw[idx] != 0x0B:
                    idx, ins = spec_binary_instr(raw, idx)
                    instar2 += [ins]
                # return idx+1, ["if",rt,instar+[["else"]],instar2+[["end"]]] #+[["end"]]
            return (
                idx + 1,
                ["if", rt, instar + [["else"]], instar2 + [["end"]]],
            )  # +[["end"]]
            # return idx+1, ["if",rt,instar+[["end"]]] #+[["end"]]
        else:
            # TODO: open ended loop
            while raw[idx] != 0x0B:
                idx, ins = spec_binary_instr(raw, idx)
                instar += [ins]
            return idx + 1, [instr_text, rt, instar + [["end"]]]  # +[["end"]]
    elif instr_text in {"br", "br_if"}:  # br, br_if
        idx, l = spec_binary_labelidx(raw, idx)
        return idx, [instr_text, l]
    elif instr_text == "br_table":  # br_table
        idx, lstar = spec_binary_vec(raw, idx, spec_binary_labelidx)
        idx, lN = spec_binary_labelidx(raw, idx)
        return idx, ["br_table", lstar, lN]
    elif instr_text in {"call", "call_indirect"}:  # call, call_indirect
        if instr_text == "call":
            idx, x = spec_binary_funcidx(raw, idx)
        if instr_text == "call_indirect":
            idx, x = spec_binary_typeidx(raw, idx)
            if raw[idx] != 0x00:
                raise MalformedModule("malformed")
            idx += 1
        return idx, [instr_text, x]
    elif 0x20 <= instr_binary <= 0x22:  # get_local, etc
        idx, x = spec_binary_localidx(raw, idx)
        return idx, [instr_text, x]
    elif 0x23 <= instr_binary <= 0x24:  # get_global, etc
        idx, x = spec_binary_globalidx(raw, idx)
        return idx, [instr_text, x]
    elif 0x28 <= instr_binary <= 0x3E:  # i32.load, i64.store, etc
        idx, m = spec_binary_memarg(raw, idx)
        return idx, [instr_text, m]
    elif 0x3F <= instr_binary <= 0x40:  # current_memory, grow_memory
        if raw[idx] != 0x00:
            raise MalformedModule("malformed")
        return idx + 1, [instr_text]
    elif 0x41 <= instr_binary <= 0x42:  # i32.const, etc
        n = 0
        if instr_text == "i32.const":
            idx, n = spec_binary_iN(raw, idx, 32)
        if instr_text == "i64.const":
            idx, n = spec_binary_iN(raw, idx, 64)
        return idx, [instr_text, n]
    elif 0x43 <= instr_binary <= 0x44:  # f32.const, etc
        z = 0
        if instr_text == "f32.const":
            if len(raw) <= idx + 4:
                raise MalformedModule("malformed")
            idx, z = spec_binary_fN(raw, idx, 32)
        if instr_text == "f64.const":
            if len(raw) <= idx + 8:
                raise MalformedModule("malformed")
            idx, z = spec_binary_fN(raw, idx, 64)
        return idx, [instr_text, z]
    else:
        # otherwise no immediate
        return idx, [instr_text]


def spec_binary_instr_inv(node):
    logger.debug("spec_binary_instr_inv(%s)", node)

    if type(node[0]) == str:
        instr_bytes += bytearray([opcodes_text2binary[node[0]]])
    # the rest is for immediates
    elif node[0] in {"block", "loop", "if"}:  # block, loop, if
        instr_bytes += spec_binary_blocktype_inv(node[1])
        instar_bytes = bytearray()
        for n in node[2][:-1]:
            instar_bytes += spec_binary_instr_inv(n)
        if len(node) == 4:  # if with else
            instar_bytes += bytearray([0x05])
            for n in node[3][:-1]:
                instar_bytes += spec_binary_instr_inv(n)
        instar_bytes += bytes([0x0B])
        instr_bytes += instar_bytes
    elif node[0] in {"br", "br_if"}:  # br, br_if
        instr_bytes += spec_binary_labelidx_inv(node[1])
    elif node[0] == "br_table":  # br_table
        instr_bytes += spec_binary_vec_inv(node[1], spec_binary_labelidx_inv)
        instr_bytes += spec_binary_labelidx_inv(node[2])
    elif node[0] == "call":  # call
        instr_bytes += spec_binary_funcidx_inv(node[1])
    elif node[0] == "call_indirect":  # call_indirect
        instr_bytes += spec_binary_typeidx_inv(node[1])
        instr_bytes += bytearray([0x00])
    elif (
        0x20 <= opcodes_text2binary[node[0]] <= 0x24
    ):  # get_local, set_local, tee_local
        instr_bytes += spec_binary_localidx_inv(node[1])
    elif 0x20 <= opcodes_text2binary[node[0]] <= 0x24:  # get_global, set_global
        instr_bytes += spec_binary_globalidx_inv(node[1])
    elif (
        0x28 <= opcodes_text2binary[node[0]] <= 0x3E
    ):  # i32.load, i32.load8_s, i64.store, etc
        instr_bytes += spec_binary_memarg_inv(node[1])
    elif 0x3F <= opcodes_text2binary[node[0]] <= 0x40:  # memory.size, memory.grow
        instr_bytes += bytearray([0x00])
    elif node[0] == "i32.const":  # i32.const
        instr_bytes += spec_binary_iN_inv(node[1], 32)
    elif node[0] == "i64.const":  # i64.const
        instr_bytes += spec_binary_iN_inv(node[1], 64)
    elif node[0] == "f32.const":  # i64.const
        instr_bytes += spec_binary_fN_inv(node[1], 32)
    elif node[0] == "f64.const":  # i64.const
        instr_bytes += spec_binary_fN_inv(node[1], 64)
    else:
        raise Exception("Invariant: unreachable code path")
    return instr_bytes


# 5.4.6 EXPRESSIONS


def spec_binary_expr(raw, idx):
    instar = []

    # TODO: open ended loop
    while raw[idx] != 0x0B:
        idx, ins = spec_binary_instr(raw, idx)
        instar += [ins]

    if raw[idx] != 0x0B:
        return idx, None  # error

    return idx + 1, instar + [["end"]]


def spec_binary_expr_inv(node):
    instar_bytes = bytearray()

    for n in node:
        instar_bytes += spec_binary_instr_inv(n)

    return instar_bytes


#############
# 5.5 MODULES
#############

# 5.5.1 INDICES


def spec_binary_typeidx(raw, idx):
    idx, x = spec_binary_uN(raw, idx, 32)
    return idx, x


def spec_binary_typeidx_inv(node):
    return spec_binary_uN_inv(node, 32)


def spec_binary_funcidx(raw, idx):
    idx, x = spec_binary_uN(raw, idx, 32)
    return idx, x


def spec_binary_funcidx_inv(node):
    return spec_binary_uN_inv(node, 32)


def spec_binary_tableidx(raw, idx):
    idx, x = spec_binary_uN(raw, idx, 32)
    return idx, x


def spec_binary_tableidx_inv(node):
    return spec_binary_uN_inv(node, 32)


def spec_binary_memidx(raw, idx):
    idx, x = spec_binary_uN(raw, idx, 32)
    return idx, x


def spec_binary_memidx_inv(node):
    return spec_binary_uN_inv(node, 32)


def spec_binary_globalidx(raw, idx):
    idx, x = spec_binary_uN(raw, idx, 32)
    return idx, x


def spec_binary_globalidx_inv(node):
    return spec_binary_uN_inv(node, 32)


def spec_binary_localidx(raw, idx):
    idx, x = spec_binary_uN(raw, idx, 32)
    return idx, x


def spec_binary_localidx_inv(node):
    return spec_binary_uN_inv(node, 32)


def spec_binary_labelidx(raw, idx):
    idx, l = spec_binary_uN(raw, idx, 32)
    return idx, l


def spec_binary_labelidx_inv(node):
    return spec_binary_uN_inv(node, 32)


# 5.5.2 SECTIONS


def spec_binary_sectionN(raw, idx, N, B, skip):
    if idx >= len(raw):
        return idx, []  # already at end
    elif raw[idx] != N:
        return idx, []  # this sec not included

    idx += 1
    idx, size = spec_binary_uN(raw, idx, 32)
    idx_plus_size = idx + size

    if skip:
        return idx + size, []
    elif N == 0:  # custom section
        idx, ret = B(raw, idx, idx + size)
    elif N == 8:  # start section
        idx, ret = B(raw, idx)
    else:
        idx, ret = spec_binary_vec(raw, idx, B)

    if idx != idx_plus_size:
        raise MalformedModule("malformed")
    return idx, ret


def spec_binary_sectionN_inv(cont, Binv, N):
    if cont == None or cont == []:
        return bytearray([])
    N_bytes = bytearray([N])
    cont_bytes = bytearray()
    if N == 8:  # startsec
        cont_bytes = Binv(cont)
    else:
        cont_bytes = spec_binary_vec_inv(cont, Binv)
    size_bytes = spec_binary_uN_inv(len(cont_bytes), 32)
    return N_bytes + size_bytes + cont_bytes


# 5.5.3 CUSTOM SECTION


def spec_binary_customsec(raw, idx, skip):
    customsecstar = []
    idx, customsec = spec_binary_sectionN(raw, idx, 0, spec_binary_custom, skip)
    return idx, customsec


def spec_binary_custom(raw, idx, endidx):
    bytestar = bytearray()
    idx, name = spec_binary_name(raw, idx)
    while idx < endidx:
        idx, byte = spec_binary_byte(raw, idx)
        bytestar += bytearray([byte])
        if idx != endidx:
            idx += 1
    return idx, [name, bytestar]


def spec_binary_customsec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_custom_inv)


def spec_binary_custom_inv(node):
    return spec_binary_name_inv(node[0]) + spec_binary_byte_inv(node[1])  # check this


# 5.5.4 TYPE SECTION


def spec_binary_typesec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 1, spec_binary_functype, skip)


def spec_binary_typesec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_functype_inv, 1)


# 5.5.5 IMPORT SECTION


def spec_binary_importsec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 2, spec_binary_import, skip)


def spec_binary_import(raw, idx):
    idx, mod = spec_binary_name(raw, idx)
    idx, nm = spec_binary_name(raw, idx)
    idx, d = spec_binary_importdesc(raw, idx)
    return idx, {"module": mod, "name": nm, "desc": d}


def spec_binary_importdesc(raw, idx):
    if raw[idx] == 0x00:
        idx, x = spec_binary_typeidx(raw, idx + 1)
        return idx, ["func", x]
    elif raw[idx] == 0x01:
        idx, tt = spec_binary_tabletype(raw, idx + 1)
        return idx, ["table", tt]
    elif raw[idx] == 0x02:
        idx, mt = spec_binary_memtype(raw, idx + 1)
        return idx, ["mem", mt]
    elif raw[idx] == 0x03:
        idx, gt = spec_binary_globaltype(raw, idx + 1)
        return idx, ["global", gt]
    else:
        raise Exception("Invariant: unreachable code path")


def spec_binary_importsec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_import_inv, 2)


def spec_binary_import_inv(node):
    return (
        spec_binary_name_inv(node["module"])
        + spec_binary_name_inv(node["name"])
        + spec_binary_importdesc_inv(node["desc"])
    )


def spec_binary_importdesc_inv(node):
    key = node[0]
    if key == "func":
        return bytearray([0x00]) + spec_binary_typeidx_inv(node[1])
    elif key == "table":
        return bytearray([0x01]) + spec_binary_tabletype_inv(node[1])
    elif key == "mem":
        return bytearray([0x02]) + spec_binary_memtype_inv(node[1])
    elif key == "global":
        return bytearray([0x03]) + spec_binary_globaltype_inv(node[1])
    else:
        return bytearray()


# 5.5.6 FUNCTION SECTION


def spec_binary_funcsec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 3, spec_binary_typeidx, skip)


def spec_binary_funcsec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_typeidx_inv, 3)


# 5.5.7 TABLE SECTION


def spec_binary_tablesec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 4, spec_binary_table, skip)


def spec_binary_table(raw, idx):
    idx, tt = spec_binary_tabletype(raw, idx)
    return idx, {"type": tt}


def spec_binary_tablesec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_table_inv, 4)


def spec_binary_table_inv(node):
    return spec_binary_tabletype_inv(node["type"])


# 5.5.8 MEMORY SECTION


def spec_binary_memsec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 5, spec_binary_mem, skip)


def spec_binary_mem(raw, idx):
    idx, mt = spec_binary_memtype(raw, idx)
    return idx, {"type": mt}


def spec_binary_memsec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_mem_inv, 5)


def spec_binary_mem_inv(node):
    return spec_binary_memtype_inv(node["type"])


# 5.5.9 GLOBAL SECTION


def spec_binary_globalsec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 6, spec_binary_global, skip)


def spec_binary_global(raw, idx):
    idx, gt = spec_binary_globaltype(raw, idx)
    idx, e = spec_binary_expr(raw, idx)
    return idx, {"type": gt, "init": e}


def spec_binary_globalsec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_global_inv, 6)


def spec_binary_global_inv(node):
    return spec_binary_globaltype_inv(node["type"]) + spec_binary_expr_inv(node["init"])


# 5.5.10 EXPORT SECTION


def spec_binary_exportsec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 7, spec_binary_export, skip)


def spec_binary_export(raw, idx):
    idx, nm = spec_binary_name(raw, idx)
    idx, d = spec_binary_exportdesc(raw, idx)
    return idx, {"name": nm, "desc": d}


def spec_binary_exportdesc(raw, idx):
    if raw[idx] == 0x00:
        idx, x = spec_binary_funcidx(raw, idx + 1)
        return idx, ["func", x]
    elif raw[idx] == 0x01:
        idx, x = spec_binary_tableidx(raw, idx + 1)
        return idx, ["table", x]
    elif raw[idx] == 0x02:
        idx, x = spec_binary_memidx(raw, idx + 1)
        return idx, ["mem", x]
    elif raw[idx] == 0x03:
        idx, x = spec_binary_globalidx(raw, idx + 1)
        return idx, ["global", x]
    else:
        raise Exception("Unreachable code path")


def spec_binary_exportsec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_export_inv, 7)


def spec_binary_export_inv(node):
    return spec_binary_name_inv(node["name"]) + spec_binary_exportdesc_inv(node["desc"])


def spec_binary_exportdesc_inv(node):
    key = node[0]
    if key == "func":
        return bytearray([0x00]) + spec_binary_funcidx_inv(node[1])
    elif key == "table":
        return bytearray([0x01]) + spec_binary_tableidx_inv(node[1])
    elif key == "mem":
        return bytearray([0x02]) + spec_binary_memidx_inv(node[1])
    elif key == "global":
        return bytearray([0x03]) + spec_binary_globalidx_inv(node[1])
    else:
        return bytearray()


# 5.5.11 START SECTION


def spec_binary_startsec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 8, spec_binary_start, skip)


def spec_binary_start(raw, idx):
    idx, x = spec_binary_funcidx(raw, idx)
    return idx, {"func": x}


def spec_binary_startsec_inv(node):
    if node == []:
        return bytearray()
    else:
        return spec_binary_sectionN_inv(node, spec_binary_start_inv, 8)


def spec_binary_start_inv(node):
    key = list(node.keys())[0]
    if key == "func":
        return spec_binary_funcidx_inv(node[1])
    else:
        return bytearray()


# 5.5.12 ELEMENT SECTION


def spec_binary_elemsec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 9, spec_binary_elem, skip)


def spec_binary_elem(raw, idx):
    idx, x = spec_binary_tableidx(raw, idx)
    idx, e = spec_binary_expr(raw, idx)
    idx, ystar = spec_binary_vec(raw, idx, spec_binary_funcidx)
    return idx, {"table": x, "offset": e, "init": ystar}


def spec_binary_elemsec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_elem_inv, 9)


def spec_binary_elem_inv(node):
    return (
        spec_binary_tableidx_inv(node["table"])
        + spec_binary_expr_inv(node["offset"])
        + spec_binary_vec_inv(node["init"], spec_binary_funcidx_inv)
    )


# 5.5.13 CODE SECTION


def spec_binary_codesec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 10, spec_binary_code, skip)


def spec_binary_code(raw, idx):
    idx, size = spec_binary_uN(raw, idx, 32)
    idx_end = idx + size
    idx, code = spec_binary_func(raw, idx)

    if idx_end != idx:
        raise MalformedModule("malformed")
    elif len(code) >= constants.UINT32_CEIL:
        raise MalformedModule("malformed")
    else:
        return idx, code


def spec_binary_func(raw, idx):
    idx, tstarstar = spec_binary_vec(raw, idx, spec_binary_locals)
    num_locals = sum(locals_info.num for locals_info in tstarstar)
    if num_locals >= constants.UINT32_CEIL:
        raise MalformedModule("malformed")
    idx, e = spec_binary_expr(raw, idx)
    concattstarstar = [
        locals_info.type_
        for locals_info
        in tstarstar
        for _ in range(locals_info.num)
    ]
    return idx, [concattstarstar, e]


class LocalsInfo(NamedTuple):
    num: int
    type_: str


def spec_binary_locals(raw, idx):
    idx, num = spec_binary_uN(raw, idx, 32)
    idx, type_ = spec_binary_valtype(raw, idx)
    return idx, LocalsInfo(num, type_)


def spec_binary_codesec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_code_inv, 10)


def spec_binary_code_inv(node):
    func_bytes = spec_binary_func_inv(node)
    return spec_binary_uN_inv(len(func_bytes), 32) + func_bytes


def spec_binary_func_inv(node):
    # group locals into chunks
    locals_ = []
    prev_valtype = ""
    for valtype in node[0]:
        if valtype == prev_valtype:
            locals_[-1][0] += 1
        else:
            locals_ += [[1, valtype]]
            prev_valtype = valtype
    locals_bytes = spec_binary_vec_inv(locals_, spec_binary_locals_inv)
    expr_bytes = spec_binary_expr_inv(node[1])
    return locals_bytes + expr_bytes


def spec_binary_locals_inv(node):
    return spec_binary_uN_inv(node[0], 32) + spec_binary_valtype_inv(node[1])


# 5.5.14 DATA SECTION


def spec_binary_datasec(raw, idx, skip=0):
    return spec_binary_sectionN(raw, idx, 11, spec_binary_data, skip)


def spec_binary_data(raw, idx):
    idx, x = spec_binary_memidx(raw, idx)
    idx, e = spec_binary_expr(raw, idx)
    idx, bstar = spec_binary_vec(raw, idx, spec_binary_byte)
    return idx, {"data": x, "offset": e, "init": bstar}


def spec_binary_datasec_inv(node):
    return spec_binary_sectionN_inv(node, spec_binary_data_inv, 11)


def spec_binary_data_inv(node):
    return (
        spec_binary_memidx_inv(node["data"])
        + spec_binary_expr_inv(node["offset"])
        + spec_binary_vec_inv(node["init"], spec_binary_byte_inv)
    )


# 5.5.15 MODULES


def spec_binary_module(raw):
    idx = 0
    magic = [0x00, 0x61, 0x73, 0x6D]
    if magic != [x for x in raw[idx : idx + 4]]:
        raise MalformedModule("malformed")
    idx += 4
    version = [0x01, 0x00, 0x00, 0x00]
    if version != [x for x in raw[idx : idx + 4]]:
        raise MalformedModule("malformed")
    idx += 4

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, functypestar = spec_binary_typesec(raw, idx, 0)
    logger.debug("functypestar: %s", functypestar)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, importstar = spec_binary_importsec(raw, idx, 0)
    logger.debug("importstar: %s", importstar)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, typeidxn = spec_binary_funcsec(raw, idx, 0)
    logger.debug("typeidxn: %s", typeidxn)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, tablestar = spec_binary_tablesec(raw, idx, 0)
    logger.debug("tablestar: %s", tablestar)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, memstar = spec_binary_memsec(raw, idx, 0)
    logger.debug("memstar: %s", memstar)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, globalstar = spec_binary_globalsec(raw, idx, 0)
    logger.debug("globalstar: %s", globalstar)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, exportstar = spec_binary_exportsec(raw, idx, 0)
    logger.debug("exportstar: %s", exportstar)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, startq = spec_binary_startsec(raw, idx, 0)
    logger.debug("startq: %s", startq)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, elemstar = spec_binary_elemsec(raw, idx, 0)
    logger.debug("elemstar: %s", elemstar)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, coden = spec_binary_codesec(raw, idx, 0)
    logger.debug("coden: %s", coden)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    idx, datastar = spec_binary_datasec(raw, idx, 0)
    logger.debug("datastar: %s", datastar)

    while idx < len(raw) and raw[idx] == 0:
        idx, customsec = spec_binary_customsec(raw, idx, 0)

    # TODO: It appears that this function incorrectly exits early once it
    # encounters an invalid section id.  See `tests/custom.wast`.

    funcn = []
    if typeidxn and coden and len(typeidxn) == len(coden):
        for i in range(len(typeidxn)):
            funcn += [{"type": typeidxn[i], "locals": coden[i][0], "body": coden[i][1]}]
    mod = {
        "types": functypestar,
        "funcs": funcn,
        "tables": tablestar,
        "mems": memstar,
        "globals": globalstar,
        "elem": elemstar,
        "data": datastar,
        "start": startq,
        "imports": importstar,
        "exports": exportstar,
    }
    return mod


def spec_binary_module_inv_to_file(mod, filename):
    f = open(filename, "wb")
    magic = bytes([0x00, 0x61, 0x73, 0x6D])
    version = bytes([0x01, 0x00, 0x00, 0x00])
    f.write(magic)
    f.write(version)
    f.write(spec_binary_typesec_inv(mod["types"]))
    f.write(spec_binary_importsec_inv(mod["imports"]))
    f.write(spec_binary_funcsec_inv([e["type"] for e in mod["funcs"]]))
    f.write(spec_binary_tablesec_inv(mod["tables"]))
    f.write(spec_binary_memsec_inv(mod["mems"]))
    f.write(spec_binary_globalsec_inv(mod["globals"]))
    f.write(spec_binary_exportsec_inv(mod["exports"]))
    f.write(spec_binary_startsec_inv(mod["start"]))
    f.write(spec_binary_elemsec_inv(mod["elem"]))
    f.write(spec_binary_codesec_inv([(f["locals"], f["body"]) for f in mod["funcs"]]))
    f.write(spec_binary_datasec_inv(mod["data"]))
    f.close()


##############
##############
# 7 APPENDIX #
##############
##############

# Chapter 7 is the Appendix. It defines a standard embedding, and a validation algorithm.

###############
# 7.1 EMBEDDING
###############

# THE FOLLOWING IS THE API, HOPEFULLY NO FUNCTIONS ABOVE IS CALLED DIRECTLY

# 7.1.1 STORE


def init_store():
    return {"funcs": [], "mems": [], "tables": [], "globals": []}


# 7.1.2 MODULES


def decode_module(bytestar):
    return spec_binary_module(bytestar)


def parse_module(codepointstar):
    raise NotImplementedError("Text parser not yet implemented")


def validate_module(module):
    spec_validate_module(module)


def instantiate_module(store, module, externvalstar):
    # TODO: handle spec deviation if necessary
    # we deviate from the spec by also returning the return value
    ret = spec_instantiate(store, module, externvalstar)

    store, F, startret = ret
    modinst = F["module"]
    return store, modinst, startret


def module_imports(module):
    ret = spec_validate_module(mod)

    externtypestar, extertypeprimestar = ret
    importstar = module["imports"]
    if len(importstar) != len(externtypestar):
        raise InvalidModule(
            f"Wrong import length: expected {len(extertypeprimestar)} / got "
            f"{len(externtypestar)}"
        )
    result = []
    for i in range(len(importstar)):
        importi = importstar[i]
        externtypei = externtypestar[i]
        resutli = [immporti["module"], importi["name"], externtypei]
        result += resulti
    return result


def module_exports(module):
    ret = spec_validate_module(mod)

    externtypestar, extertypeprimestar = ret
    exportstar = module["exports"]

    if len(exportstar) != len(externtypeprimestar):
        raise Exception("TODO: proper error message")

    result = []
    for i in range(len(importstar)):
        exporti = exportstar[i]
        externtypeprimei = externtypeprimestar[i]
        resutli = [exporti["name"], externtypeprimei]
        result += resulti
    return result


# 7.1.3 EXPORTS


def get_export(moduleinst, name):
    # assume valid so all export names are unique
    for exportinsti in moduleinst["exports"]:
        if name == exportinsti["name"]:
            return exportinsti["value"]
    else:
        known_module_names = sorted(set(m['name'] for m in moduleinst["exports"]))
        raise ValidationError(
            f"No module found with name `{name}`.  Known module names: "
            f"{'|'.join(known_module_names)}"
        )


# 7.1.4 FUNCTIONS


def alloc_func(store, functype, hostfunc):
    store, funcaddr = spec_allochostfunc(store, functype, hostfunc)
    return store, funcaddr


def type_func(store, funcaddr):
    if len(store["funcs"]) <= funcaddr:
        raise ValidationError(
            f"Function address outside of allowed range: {funcaddr} > "
            f"{len(store['funcs'])}"
        )
    functype = store["funcs"][funcaddr]
    return functype


def invoke_func(store, funcaddr, valstar):
    ret = spec_invoke(store, funcaddr, valstar)
    return store, ret


# 7.1.4 TABLES


def alloc_table(store, tabletype):
    store, tableaddr = spec_alloctable(store, tabletype)
    return store, tableaddr


def type_table(store, tableaddr):
    if len(store["tables"]) <= tableaddr:
        raise ValidationError(
            f"Table address outside of allowed range: {tableaddr} > "
            f"{len(store['tables'])}"
        )
    tableinst = store["tables"][tableaddr]
    max_ = tableinst["max"]
    min_ = len(tableinst["elem"])  # TODO: is this min OK?
    tabletype = [{"min": min_, "max": max_}, "anyfunc"]
    return tabletype


def read_table(store, tableaddr, i):
    if len(store["tables"]) <= tableaddr:
        raise ValidationError(
            f"Table address outside of allowed range: {tableaddr} > "
            f"{len(store['tables'])}"
        )
    if type(i) != int or i < 0:
        raise ValidationError(
            f"Invalid table index.  Must be positive integer.  Got {repr(i)}"
        )
    ti = store["tables"][tableaddr]
    if i >= len(ti["elem"]):
        raise ValidationError(
            f"Index out of range for table.  {i} >= {len(ti['elem'])}"
        )
    return ti["elem"][i]


def write_table(store, tableaddr, i, funcaddr):
    if len(store["tables"]) <= tableaddr:
        raise ValidationError(
            f"Table address outside of allowed range: {tableaddr} > "
            f"{len(store['tables'])}"
        )
    if type(i) != int or i < 0:
        raise ValidationError(
            f"Invalid table index.  Must be positive integer.  Got {repr(i)}"
        )
    ti = store["tables"][tableaddr]
    if i >= len(ti["elem"]):
        raise ValidationError(
            f"Index out of range for table.  {i} >= {len(ti['elem'])}"
        )
    ti["elem"][i] = funcaddr
    return store


def size_table(store, tableaddr):
    if len(store["tables"]) <= tableaddr:
        raise ValidationError(
            f"Table address outside of allowed range: {tableaddr} > "
            f"{len(store['tables'])}"
        )
    return len(store["tables"][tableaddr]["elem"])


def grow_table(store, tableaddr, n):
    if len(store["tables"]) <= tableaddr:
        raise ValidationError(
            f"Table address outside of allowed range: {tableaddr} > "
            f"{len(store['tables'])}"
        )
    elif type(n) != int or n < 0:
        raise ValidationError(
            f"Invalid table index.  Must be positive integer.  Got {repr(i)}"
        )

    spec_growtable(store["tabless"][tableaddr], n)

    return store


# 7.1.6 MEMORIES


def alloc_mem(store, memtype):
    store, memaddr = spec_allocmem(store, memtype)
    return store, memaddr


def type_mem(store, memaddr):
    if len(store["mems"]) <= memaddr:
        raise ValidationError(
            f"Memory address outside of allowed range: {memaddr} > "
            f"{len(store['mems'])}"
        )
    meminst = store["mems"][memaddr]
    max_ = meminst["max"]
    min_ = (
        len(meminst["data"]) // constants.PAGE_SIZE_64K
    )  #TODO: is this min OK?


def read_mem(store, memaddr, i):
    if len(store["mems"]) <= memaddr:
        raise ValidationError(
            f"Memory address outside of allowed range: {memaddr} > "
            f"{len(store['mems'])}"
        )
    elif type(i) != int or i < 0:
        raise ValidationError(
            f"Invalid memory index.  Must be positive integer.  Got {repr(i)}"
        )

    mi = store["mems"][memaddr]

    if i >= len(mi["data"]):
        raise ValidationError(
            f"Memory index out of bounds.  {i} >= {len(mi['data'])}"
        )
    else:
        return mi["data"][i]


def write_mem(store, memaddr, i, byte):
    if len(store["mems"]) <= memaddr:
        raise ValidationError(
            f"Memory address outside of allowed range: {memaddr} > "
            f"{len(store['mems'])}"
        )
    elif type(i) != int or i < 0:
        raise ValidationError(
            f"Invalid memory index.  Must be positive integer.  Got {repr(i)}"
        )

    mi = store["mems"][memaddr]
    if i >= len(mi["data"]):
        raise ValidationError(
            f"Memory index out of bounds.  {i} >= {len(mi['data'])}"
        )
    mi["data"][i] = byte
    return store


def size_mem(store, memaddr):
    if len(store["mems"]) <= memaddr:
        raise ValidationError(
            f"Memory address outside of allowed range: {memaddr} > "
            f"{len(store['mems'])}"
        )
    return len(store["mems"][memaddr]) // constants.PAGE_SIZE_64K


def grow_mem(store, memaddr, n):
    if len(store["mems"]) <= memaddr:
        raise ValidationError(
            f"Memory address outside of allowed range: {memaddr} > "
            f"{len(store['mems'])}"
        )
    elif type(n) != int or n < 0:
        raise ValidationError(
            f"Invalid memory index.  Must be positive integer.  Got {repr(i)}"
        )

    spec_growmem(store["mems"][memaddr], n)

    return store


# 7.1.7 GLOBALS


def alloc_global(store, globaltype, val):
    return spec_allocglobal(store, globaltype, val)


def type_global(store, globaladdr):
    if len(store["globals"]) <= globaladdr:
        raise ValidationError(
            f"Globals address outside of allowed range: {globaladdr} > "
            f"{len(store['globals'])}"
        )
    globalinst = store["globals"][globaladdr]
    mut = globalinst["mut"]
    valtype = globalinst["value"][0]
    return [mut, valtype]


def read_global(store, globaladdr):
    if len(store["globals"]) <= globaladdr:
        raise ValidationError(
            f"Globals address outside of allowed range: {globaladdr} > "
            f"{len(store['globals'])}"
        )
    gi = store["globals"][globaladdr]
    return gi["value"]


# arg must look like ["i32.const",5]
def write_global(store, globaladdr, val):
    if len(store["globals"]) <= globaladdr:
        raise ValidationError(
            f"Globals address outside of allowed range: {globaladdr} > "
            f"{len(store['globals'])}"
        )
    # TODO: type check; handle val without type
    gi = store["globals"][globaladdr]
    if gi["mut"] != "var":
        raise ValidationError("Attempt to write to an immutable global variable at address '{globaladdr}'")
    gi["value"] = val
    return store


##########################
# 7.3 VALIDATION ALGORITHM
##########################

# 7.3.1 DATA STRUCTURES

# Conventions:
#   the spec makes opds and ctrls global variables, but we pass them around as arguments
#   the control stack is a python list, which allows fast appending but not prepending. So the spec's index 0 corresponds to python list idx -1, and eg spec idx 3 corresponds to our python list idx -1-3 ie -4
#   the spec offers two ways to keep track of labels, using C.labels in ch 3 or a control stack in the appendix. Here we use the appendix method


def spec_push_opd(opds, type_):
    opds.append(type_)


def spec_pop_opd(opds, ctrls):
    # check if underflows current block, and returns one type but if underflows
    # and unreachable, which can happen if unconditional branch, when stack is
    # typed polymorphically, operands are still pushed and popped to check if
    # code after unreachable is valid, polymorphic stack can't underflow
    if len(opds) == ctrls[-1]["height"] and ctrls[-1]["unreachable"]:
        # TODO: remove magic values.
        return "Unknown"
    elif len(opds) == ctrls[-1]["height"]:
        raise InvalidModule("invalid")  # error
    elif len(opds) == 0:
        raise InvalidModule("invalid")  # error, not in spec
    else:
        to_return = opds[-1]
        del opds[-1]
        return to_return


def spec_pop_opd_expect(opds, ctrls, expect):
    actual = spec_pop_opd(opds, ctrls)
    if actual == -1:
        raise InvalidModule("invalid")  # error
    # in case one is unknown, the more specific one is returned
    elif actual == "Unknown":
        return expect
    elif expect == "Unknown":
        return actual
    elif actual != expect:
        raise InvalidModule("invalid")  # error
    else:
        return actual


def spec_push_opds(opds, ctrls, types):
    for t in types:
        spec_push_opd(opds, t)
    return 0


def spec_pop_opds_expect(opds, ctrls, types):
    if types:
        for t in reversed(types):
            r = spec_pop_opd_expect(opds, ctrls, t)
        return r
    else:
        return None


def spec_ctrl_frame(label_types, end_types, height, unreachable):
    # args are:
    #   label_types: type of the branch's label, to type-check branches
    #   end_types: result type of the branch, currently Wasm spec allows at most one return value
    #   height: height of opd_stack at start of block, to check that operands do not underflow current block
    #   unreachable: whether remainder of block is unreachable, to handle stack-polymorphic typing after branches
    return {
        "label_types": label_types,
        "end_types": end_types,
        "height": height,
        "unreachable": unreachable,
    }


def spec_push_ctrl(opds, ctrls, label, out):
    frame = {
        "label_types": label,
        "end_types": out,
        "height": len(opds),
        "unreachable": False,
    }
    ctrls.append(frame)


def spec_pop_ctrl(opds, ctrls):
    if len(ctrls) < 1:
        raise InvalidModule("invalid")  # error
    frame = ctrls[-1]
    # verify opd stack has right types to exit block, and pops them
    r = spec_pop_opds_expect(opds, ctrls, frame["end_types"])
    if r == -1:
        raise InvalidModule("invalid")  # error
    # make shure stack is back to original height
    if len(opds) != frame["height"]:
        raise InvalidModule("invalid")  # error
    del ctrls[-1]
    return frame["end_types"]


# extra underscore since spec_unreachable() is used in chapter 4
def spec_unreachable_(opds, ctrls):
    # purge from operand stack, allows stack-polymorphic logic in pop_opd() take effect
    del opds[ctrls[-1]["height"] :]
    ctrls[-1]["unreachable"] = True


# 7.3.2 VALIDATION OF OPCODE SEQUENCES

# validate a single opcode based on current context C, operand stack opds, and control stack ctrls
def spec_validate_opcode(C, opds, ctrls, opcode, immediates):
    logger.debug("spec_validate_opcode(%s, %s, %s, %s, %s)", C, opds, ctrls, opcode, immediates)
    # C is the context
    # opds is the operand stack
    # ctrls is the control stack
    opcode_binary = opcodes_text2binary[opcode]
    if 0x00 <= opcode_binary <= 0x11:  # CONTROL INSTRUCTIONS
        if opcode_binary == 0x00:  # unreachable
            spec_unreachable_(opds, ctrls)
        elif opcode_binary == 0x01:  # nop
            pass
        elif opcode_binary <= 0x04:  # block, loop, if
            rt = immediates
            if rt != [] and type(rt) != list:
                rt = [rt]  # TODO: clean this up, works but ugly
            if opcode_binary == 0x02:  # block
                spec_push_ctrl(opds, ctrls, rt, rt)
            elif opcode_binary == 0x03:  # loop
                spec_push_ctrl(opds, ctrls, [], rt)
            else:  # if
                spec_pop_opd_expect(opds, ctrls, constants.INT32)
                spec_push_ctrl(opds, ctrls, rt, rt)
        elif opcode_binary == 0x05:  # else
            results = spec_pop_ctrl(opds, ctrls)
            if results != [] and type(results) != list:
                results = [results]
            spec_push_ctrl(opds, ctrls, results, results)
        elif opcode_binary == 0x0B:  # end
            results = spec_pop_ctrl(opds, ctrls)
            spec_push_opds(opds, ctrls, results)
        elif opcode_binary == 0x0C:  # br
            n = immediates
            if n == None:
                raise InvalidModule("invalid")
            elif len(ctrls) <= n:
                raise InvalidModule("invalid")
            spec_pop_opds_expect(opds, ctrls, ctrls[-1 - n]["label_types"])
            spec_unreachable_(opds, ctrls)
        elif opcode_binary == 0x0D:  # br_if
            n = immediates
            if n == None:
                raise InvalidModule("invalid")
            elif len(ctrls) <= n:
                raise InvalidModule("invalid")
            spec_pop_opd_expect(opds, ctrls, constants.INT32)
            spec_pop_opds_expect(opds, ctrls, ctrls[-1 - n]["label_types"])
            spec_push_opds(opds, ctrls, ctrls[-1 - n]["label_types"])
        elif opcode_binary == 0x0E:  # br_table
            nstar = immediates[0]
            m = immediates[1]
            if len(ctrls) <= m:
                raise InvalidModule("invalid")
            for n in nstar:
                if (
                    len(ctrls) <= n
                    or ctrls[-1 - n]["label_types"] != ctrls[-1 - m]["label_types"]
                ):
                    raise InvalidModule("invalid")
            spec_pop_opd_expect(opds, ctrls, constants.INT32)
            spec_pop_opds_expect(opds, ctrls, ctrls[-1 - m]["label_types"])
            spec_unreachable_(opds, ctrls)
        elif opcode_binary == 0x0F:  # return
            if "return" not in C:
                raise InvalidModule("invalid")
            t = C["return"]
            spec_pop_opds_expect(opds, ctrls, t)
            spec_unreachable_(opds, ctrls)
        elif opcode_binary == 0x10:  # call
            x = immediates
            if ("funcs" not in C) or len(C["funcs"]) <= x:
                raise InvalidModule("invalid")
            spec_pop_opds_expect(opds, ctrls, C["funcs"][x][0])
            spec_push_opds(opds, ctrls, C["funcs"][x][1])
        elif opcode_binary == 0x11:  # call_indirect
            x = immediates
            if ("tables" not in C) or len(C["tables"]) == 0:
                raise InvalidModule("invalid")
            elif C["tables"][0][1] != "anyfunc":
                raise InvalidModule("invalid")
            elif len(C["types"]) <= x:
                raise InvalidModule("invalid")
            spec_pop_opd_expect(opds, ctrls, constants.INT32)
            spec_pop_opds_expect(opds, ctrls, C["types"][x][0])
            spec_push_opds(opds, ctrls, C["types"][x][1])
    elif 0x1A <= opcode_binary <= 0x1B:  # PARAMETRIC INSTRUCTIONS
        if opcode_binary == 0x1A:  # drop
            spec_pop_opd(opds, ctrls)
        elif opcode_binary == 0x1B:  # select
            spec_pop_opd_expect(opds, ctrls, constants.INT32)
            t1 = spec_pop_opd(opds, ctrls)
            t2 = spec_pop_opd_expect(opds, ctrls, t1)
            spec_push_opd(opds, t2)
    elif 0x20 <= opcode_binary <= 0x24:  # VARIABLE INSTRUCTIONS
        if opcode_binary == 0x20:  # get_local
            x = immediates
            if len(C["locals"]) <= x:
                raise InvalidModule("invalid")
            elif C["locals"][x] == constants.INT32:
                spec_push_opd(opds, constants.INT32)
            elif C["locals"][x] == constants.INT64:
                spec_push_opd(opds, constants.INT64)
            elif C["locals"][x] == constants.FLOAT32:
                spec_push_opd(opds, constants.FLOAT32)
            elif C["locals"][x] == constants.FLOAT64:
                spec_push_opd(opds, constants.FLOAT64)
            else:
                raise InvalidModule("invalid")
        elif opcode_binary == 0x21:  # set_local
            x = immediates
            if len(C["locals"]) <= x:
                raise InvalidModule("invalid")
            elif C["locals"][x] == constants.INT32:
                ret = spec_pop_opd_expect(opds, ctrls, constants.INT32)
            elif C["locals"][x] == constants.INT64:
                ret = spec_pop_opd_expect(opds, ctrls, constants.INT64)
            elif C["locals"][x] == constants.FLOAT32:
                ret = spec_pop_opd_expect(opds, ctrls, constants.FLOAT32)
            elif C["locals"][x] == constants.FLOAT64:
                ret = spec_pop_opd_expect(opds, ctrls, constants.FLOAT64)
            else:
                raise InvalidModule("invalid")
        elif opcode_binary == 0x22:  # tee_local
            x = immediates
            if len(C["locals"]) <= x:
                raise InvalidModule("invalid")
            elif C["locals"][x] == constants.INT32:
                spec_pop_opd_expect(opds, ctrls, constants.INT32)
                spec_push_opd(opds, constants.INT32)
            elif C["locals"][x] == constants.INT64:
                spec_pop_opd_expect(opds, ctrls, constants.INT64)
                spec_push_opd(opds, constants.INT64)
            elif C["locals"][x] == constants.FLOAT32:
                spec_pop_opd_expect(opds, ctrls, constants.FLOAT32)
                spec_push_opd(opds, constants.FLOAT32)
            elif C["locals"][x] == constants.FLOAT64:
                spec_pop_opd_expect(opds, ctrls, constants.FLOAT64)
                spec_push_opd(opds, constants.FLOAT64)
            else:
                raise InvalidModule("invalid")
        elif opcode_binary == 0x23:  # get_global
            x = immediates
            if len(C["globals"]) <= x:
                raise InvalidModule("invalid")
            elif C["globals"][x][1] == constants.INT32:
                spec_push_opd(opds, constants.INT32)
            elif C["globals"][x][1] == constants.INT64:
                spec_push_opd(opds, constants.INT64)
            elif C["globals"][x][1] == constants.FLOAT32:
                spec_push_opd(opds, constants.FLOAT32)
            elif C["globals"][x][1] == constants.FLOAT64:
                spec_push_opd(opds, constants.FLOAT64)
            else:
                raise InvalidModule("invalid")
        elif opcode_binary == 0x24:  # set_global
            x = immediates
            if len(C["globals"]) <= x:
                raise InvalidModule("invalid")
            elif C["globals"][x][0] != "var":
                raise InvalidModule("invalid")
            elif C["globals"][x][1] == constants.INT32:
                ret = spec_pop_opd_expect(opds, ctrls, constants.INT32)
            elif C["globals"][x][1] == constants.INT64:
                ret = spec_pop_opd_expect(opds, ctrls, constants.INT64)
            elif C["globals"][x][1] == constants.FLOAT32:
                ret = spec_pop_opd_expect(opds, ctrls, constants.FLOAT32)
            elif C["globals"][x][1] == constants.FLOAT64:
                ret = spec_pop_opd_expect(opds, ctrls, constants.FLOAT64)
            else:
                raise InvalidModule("invalid")
        else:
            raise Exception(f"Unexpected opcode value: {opcode_binary}")
    elif 0x28 <= opcode_binary <= 0x40:  # MEMORY INSTRUCTIONS
        if "mems" not in C or len(C["mems"]) == 0:
            raise InvalidModule("invalid")
        elif opcode_binary <= 0x35:
            memarg = immediates
            if opcode_binary == 0x28:  # i32.load
                N = 32
                t = constants.INT32
            elif opcode_binary == 0x29:  # i64.load
                N = 64
                t = constants.INT64
            elif opcode_binary == 0x2A:  # f32.load
                N = 32
                t = constants.FLOAT32
            elif opcode_binary == 0x2B:  # f64.load
                N = 64
                t = constants.FLOAT64
            elif opcode_binary <= 0x2D:  # i32.load8_s, i32.load8_u
                N = 8
                t = constants.INT32
            elif opcode_binary <= 0x2F:  # i32.load16_s, i32.load16_u
                N = 16
                t = constants.INT32
            elif opcode_binary <= 0x31:  # i64.load8_s, i64.load8_u
                N = 8
                t = constants.INT64
            elif opcode_binary <= 0x33:  # i64.load16_s, i64.load16_u
                N = 16
                t = constants.INT64
            elif opcode_binary <= 0x35:  # i64.load32_s, i64.load32_u
                N = 32
                t = constants.INT64
            else:
                raise Exception(f"Unexpected opcode value: {opcode_binary}")

            if 2 ** memarg["align"] > N // 8:
                raise InvalidModule("invalid")
            spec_pop_opd_expect(opds, ctrls, constants.INT32)
            spec_push_opd(opds, t)
        elif opcode_binary <= 0x3E:
            memarg = immediates
            if opcode_binary == 0x36:  # i32.store
                N = 32
                t = constants.INT32
            elif opcode_binary == 0x37:  # i64.store
                N = 64
                t = constants.INT64
            elif opcode_binary == 0x38:  # f32.store
                N = 32
                t = constants.FLOAT32
            elif opcode_binary == 0x39:  # f64.store
                N = 64
                t = constants.FLOAT64
            elif opcode_binary == 0x3A:  # i32.store8
                N = 8
                t = constants.INT32
            elif opcode_binary == 0x3B:  # i32.store16
                N = 16
                t = constants.INT32
            elif opcode_binary == 0x3C:  # i64.store8
                N = 8
                t = constants.INT64
            elif opcode_binary == 0x3D:  # i64.store16
                N = 16
                t = constants.INT64
            elif opcode_binary == 0x3E:  # i64.store32
                N = 32
                t = constants.INT64

            if 2 ** memarg["align"] > N // 8:
                raise InvalidModule("invalid")

            spec_pop_opd_expect(opds, ctrls, t)
            spec_pop_opd_expect(opds, ctrls, constants.INT32)
        elif opcode_binary == 0x3F:  # memory.size
            spec_push_opd(opds, constants.INT32)
        elif opcode_binary == 0x40:  # memory.grow
            spec_pop_opd_expect(opds, ctrls, constants.INT32)
            spec_push_opd(opds, constants.INT32)
        else:
            raise Exception(f"Unexpected opcode value: {opcode_binary}")
    elif 0x41 <= opcode_binary <= 0xBF:  # NUMERIC INSTRUCTIONS
        if opcode_binary <= 0x44:
            if opcode_binary == 0x41:  # i32.const
                spec_push_opd(opds, constants.INT32)
            elif opcode_binary == 0x42:  # i64.const
                spec_push_opd(opds, constants.INT64)
            elif opcode_binary == 0x43:  # f32.const
                spec_push_opd(opds, constants.FLOAT32)
            else:  # f64.const
                spec_push_opd(opds, constants.FLOAT64)
        elif opcode_binary <= 0x4F:
            if opcode_binary == 0x45:  # i32.eqz
                spec_pop_opd_expect(opds, ctrls, constants.INT32)
                spec_push_opd(opds, constants.INT32)
            else:  # i32.eq, i32.ne, i32.lt_s, i32.lt_u, i32.gt_s, i32.gt_u, i32.le_s, i32.le_u, i32.ge_s, i32.ge_u
                spec_pop_opd_expect(opds, ctrls, constants.INT32)
                spec_pop_opd_expect(opds, ctrls, constants.INT32)
                spec_push_opd(opds, constants.INT32)
        elif opcode_binary <= 0x5A:
            if opcode_binary == 0x50:  # i64.eqz
                spec_pop_opd_expect(opds, ctrls, constants.INT64)
                spec_push_opd(opds, constants.INT32)
            else:  # i64.eq, i64.ne, i64.lt_s, i64.lt_u, i64.gt_s, i64.gt_u, i64.le_s, i64.le_u, i64.ge_s, i64.ge_u
                spec_pop_opd_expect(opds, ctrls, constants.INT64)
                spec_pop_opd_expect(opds, ctrls, constants.INT64)
                spec_push_opd(opds, constants.INT32)
        elif opcode_binary <= 0x60:  # f32.eq, f32.ne, f32.lt, f32.gt, f32.le, f32.ge
            spec_pop_opd_expect(opds, ctrls, constants.FLOAT32)
            spec_pop_opd_expect(opds, ctrls, constants.FLOAT32)
            spec_push_opd(opds, constants.INT32)
        elif opcode_binary <= 0x66:  # f64.eq, f64.ne, f64.lt, f64.gt, f64.le, f64.ge
            spec_pop_opd_expect(opds, ctrls, constants.FLOAT64)
            spec_pop_opd_expect(opds, ctrls, constants.FLOAT64)
            spec_push_opd(opds, constants.INT32)
        elif opcode_binary <= 0x78:
            if opcode_binary <= 0x69:  # i32.clz, i32.ctz, i32.popcnt
                spec_pop_opd_expect(opds, ctrls, constants.INT32)
                spec_push_opd(opds, constants.INT32)
            else:  # i32.add, i32.sub, i32.mul, i32.div_s, i32.div_u, i32.rem_s, i32.rem_u, i32.and, i32.or, i32.xor, i32.shl, i32.shr_s, i32.shr_u, i32.rotl, i32.rotr
                spec_pop_opd_expect(opds, ctrls, constants.INT32)
                spec_pop_opd_expect(opds, ctrls, constants.INT32)
                spec_push_opd(opds, constants.INT32)
        elif opcode_binary <= 0x8A:
            if opcode_binary <= 0x7B:  # i64.clz, i64.ctz, i64.popcnt
                spec_pop_opd_expect(opds, ctrls, constants.INT64)
                spec_push_opd(opds, constants.INT64)
            else:  # i64.add, i64.sub, i64.mul, i64.div_s, i64.div_u, i64.rem_s, i64.rem_u, i64.and, i64.or, i64.xor, i64.shl, i64.shr_s, i64.shr_u, i64.rotl, i64.rotr
                spec_pop_opd_expect(opds, ctrls, constants.INT64)
                spec_pop_opd_expect(opds, ctrls, constants.INT64)
                spec_push_opd(opds, constants.INT64)
        elif opcode_binary <= 0x98:
            if (
                opcode_binary <= 0x91
            ):  # f32.abs, f32.neg, f32.ceil, f32.floor, f32.trunc, f32.nearest, f32.sqrt,
                spec_pop_opd_expect(opds, ctrls, constants.FLOAT32)
                spec_push_opd(opds, constants.FLOAT32)
            else:  # f32.add, f32.sub, f32.mul, f32.div, f32.min, f32.max, f32.copysign
                spec_pop_opd_expect(opds, ctrls, constants.FLOAT32)
                spec_pop_opd_expect(opds, ctrls, constants.FLOAT32)
                spec_push_opd(opds, constants.FLOAT32)
        elif opcode_binary <= 0xA6:
            if (
                opcode_binary <= 0x9F
            ):  # f64.abs, f64.neg, f64.ceil, f64.floor, f64.trunc, f64.nearest, f64.sqrt,
                spec_pop_opd_expect(opds, ctrls, constants.FLOAT64)
                spec_push_opd(opds, constants.FLOAT64)
            else:  # f64.add, f64.sub, f64.mul, f64.div, f64.min, f64.max, f64.copysign
                spec_pop_opd_expect(opds, ctrls, constants.FLOAT64)
                spec_pop_opd_expect(opds, ctrls, constants.FLOAT64)
                spec_push_opd(opds, constants.FLOAT64)
        elif opcode_binary <= 0xBF:
            if opcode_binary == 0xA7:  # i32.wrap/i64
                spec_pop_opd_expect(opds, ctrls, constants.INT64)
                spec_push_opd(opds, constants.INT32)
            elif opcode_binary <= 0xA9:  # i32.trunc_s/f32, i32.trunc_u/f32
                spec_pop_opd_expect(opds, ctrls, constants.FLOAT32)
                spec_push_opd(opds, constants.INT32)
            elif opcode_binary <= 0xAB:  # i32.trunc_s/f64, i32.trunc_u/f64
                spec_pop_opd_expect(opds, ctrls, constants.FLOAT64)
                spec_push_opd(opds, constants.INT32)
            elif opcode_binary <= 0xAD:  # i64.extend_s/i32, i64.extend_u/i32
                spec_pop_opd_expect(opds, ctrls, constants.INT32)
                spec_push_opd(opds, constants.INT64)
            elif opcode_binary <= 0xAF:  # i64.trunc_s/f32, i64.trunc_u/f32
                spec_pop_opd_expect(opds, ctrls, constants.FLOAT32)
                spec_push_opd(opds, constants.INT64)
            elif opcode_binary <= 0xB1:  # i64.trunc_s/f64, i64.trunc_u/f64
                spec_pop_opd_expect(opds, ctrls, constants.FLOAT64)
                spec_push_opd(opds, constants.INT64)
            elif opcode_binary <= 0xB3:  # f32.convert_s/i32, f32.convert_u/i32
                spec_pop_opd_expect(opds, ctrls, constants.INT32)
                spec_push_opd(opds, constants.FLOAT32)
            elif opcode_binary <= 0xB5:  # f32.convert_s/i64, f32.convert_u/i64
                spec_pop_opd_expect(opds, ctrls, constants.INT64)
                spec_push_opd(opds, constants.FLOAT32)
            elif opcode_binary <= 0xB6:  # f32.demote/f64
                spec_pop_opd_expect(opds, ctrls, constants.FLOAT64)
                spec_push_opd(opds, constants.FLOAT32)
            elif opcode_binary <= 0xB8:  # f64.convert_s/i32, f64.convert_u/i32
                spec_pop_opd_expect(opds, ctrls, constants.INT32)
                spec_push_opd(opds, constants.FLOAT64)
            elif opcode_binary <= 0xBA:  # f64.convert_s/i64, f64.convert_u/i64
                spec_pop_opd_expect(opds, ctrls, constants.INT64)
                spec_push_opd(opds, constants.FLOAT64)
            elif opcode_binary == 0xBB:  # f64.promote/f32
                spec_pop_opd_expect(opds, ctrls, constants.FLOAT32)
                spec_push_opd(opds, constants.FLOAT64)
            elif opcode_binary == 0xBC:  # i32.reinterpret/f32
                spec_pop_opd_expect(opds, ctrls, constants.FLOAT32)
                spec_push_opd(opds, constants.INT32)
            elif opcode_binary == 0xBD:  # i64.reinterpret/f64
                spec_pop_opd_expect(opds, ctrls, constants.FLOAT64)
                spec_push_opd(opds, constants.INT64)
            elif opcode_binary == 0xBE:  # f32.reinterpret/i32
                spec_pop_opd_expect(opds, ctrls, constants.INT32)
                spec_push_opd(opds, constants.FLOAT32)
            elif opcode_binary == 0xBF:  # f64.reinterpret/i64
                spec_pop_opd_expect(opds, ctrls, constants.INT64)
                spec_push_opd(opds, constants.FLOAT64)
            else:
                raise Exception(f"Unexpected opcode value: {opcode_binary}")
        else:
            raise Exception(f"Unexpected opcode value: {opcode_binary}")
    return 0  # success, valid so far


# args when called the first time:
def iterate_through_expression_and_validate_each_opcode(
    expression, Context, opds, ctrls
):
    for node in expression:
        if type(node[0]) != str:
            raise InvalidModule("invalid")  # error
        opcode = node[0]
        # get immediate
        immediate = None
        if node[0] in {
            "br",
            "br_if",
            "block",
            "loop",
            "if",
            "call",
            "call_indirect",
            "get_local",
            "set_local",
            "tee_local",
            "get_global",
            "set_global",
            "i32.const",
            "i64.const",
            "f32.const",
            "f64.const",
        } or node[0][3:8] in {".load", ".stor"}:
            immediate = node[1]
        elif node[0] == "br_table":
            immediate = [node[1], node[2]]

        # validate
        spec_validate_opcode(Context, opds, ctrls, opcode, immediate)
        # recurse for block, loop, if
        if node[0] in {"block", "loop", "if"}:
            iterate_through_expression_and_validate_each_opcode(
                node[2], Context, opds, ctrls
            )
            if len(node) == 4:  # if with else
                iterate_through_expression_and_validate_each_opcode(
                    node[3], Context, opds, ctrls
                )
    return 0


##########################################################
# HELPERS TO EXECUTE THIS FILE ON COMMAND LINE ARGUMENTS #
##########################################################


def instantiate_wasm_invoke_start(filename):
    if not os.path.exists(filename):
        raise ValidationError(f"Unable to open file: {filename}")

    with open(filename, 'rb') as file_:
        bytestar = memoryview(file_.read())
        if not bytestar:
            raise ValidationError(f"Error reading file: {filename}")
        module = decode_module(bytestar)  # get module as abstract syntax

    if not module:
        raise ValidationError(f"Could not decode module: {filename}")

    store = init_store()  # do this once for each VM instance
    externvalstar = []  # imports, hopefully none
    store, moduleinst, ret = instantiate_module(store, module, externvalstar)
    return ret


def instantiate_wasm_invoke_func(filename, funcname, args):
    # TODO: DRY: this preamble is the same as the
    # `instantiate_wasm_invoke_start` preamble.
    if not os.path.exists(filename):
        raise ValidationError(f"Unable to open file: {filename}")

    with open(filename, 'rb') as file_:
        bytestar = memoryview(file_.read())
        if not bytestar:
            raise ValidationError(f"Error reading file: {filename}")
        module = decode_module(bytestar)  # get module as abstract syntax

    if not module:
        raise ValidationError(f"Could not decode module: {filename}")

    store = init_store()  # do this once for each VM instance
    externvalstar = []  # imports, hopefully none
    store, moduleinst, ret = instantiate_module(store, module, externvalstar)
    externval = get_export(moduleinst, funcname)

    if not externval or externval[0] != "func":
        raise ValidationError(
            f"No function export found for function name: '{funcname}'"
        )
    funcaddr = externval[1]
    valstar = [["i32.const", int(arg)] for arg in args]
    store, ret = invoke_func(store, funcaddr, valstar)

    if type(ret) == list and len(ret) > 0:
        ret = ret[0]
    return ret
