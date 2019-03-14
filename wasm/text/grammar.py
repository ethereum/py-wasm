import parsimonious


UNTESTED = """
script = open (_ cmd)* close

cmd =
  module /
  (open "register" string name?) /
  action /
  assertion /
  meta

assertion = open (
  ("assert_return"                _ action exprs) /
  ("assert_return_canonical_nan"  _ action) /
  ("assert_return_arithmetic_nan" _ action) /
  ("assert_trap"                  _ action _ string) /
  ("assert_malformed"             _ module _ string) /
  ("assert_invalid"               _ module _ string) /
  ("assert_unlinkable"            _ module _ string) /
  ("assert_trap"                  _ module _ string)
  ) close

action = open (
  ("invoke" _ name? _ string exprs) /
  ("get" _ name? _ string)
  ) close

meta = open (
  ("script" _ name? _ script) /
  ("input"  _ name? _ string) /
  ("output" _ name? _ string?)
  ) close


module = open (
    ("module" _ name? _ secs) /
    (                 _ secs) /
    ("module"         _ secs) /
    ("module" _ name? _ "binary" strings) /
    ("module" _ name? _ "quote" strings)
    ) close

secs = typedef* _ func* _ import* _ export* _ table? _ memory? _ global* _ elem* _ data* _ start?

start = open "start" var close

typedef = open "type" name? open "func" params result close close

import = open "import" _ string _ string _ imkind close
export = open "export" _ string _ exkind close

imkind = open (
    ("func" _ name? _ func_type) /
    ("global" _ name? _ global_type) /
    ("table" _ name? _ table_type) /
    ("memory" _ name? _ memory_type)
    ) close
exkind = open (
    ("func" _ var) /
    ("global" _ var) /
    ("table" _ var) /
    ("memory" _ var)
    ) close

data = open (
    ("data" _ var? _ open offset instrs close strings) /
    ("data" _ var? _ expr strings)
    ) close
memory = open (
    ("memory" _ name? memory_type) /
    ("memory" _ name? exports) /
    ("memory" _ name? _ open "import" _ string _ string close _ memory_type) /
    ("memory" _ name? exports_opt _ open "data" strings close)
    ) close
elem = open (
    ("elem" _ var? _ open "offset" instrs close vars) /
    ("elem" _ var? _ expr vars)
    ) close
table = open (
    ("table" _ name? _ table_type) /
    ("table" _ name? exports) /
    ("table" _ name? open "import" string _ string close table_type) /
    ("table" _ name? exports_opt _ elem_type _ open "elem" vars close)
    ) close
global = open (
    ("global" _ name? _ global_type instrs) /
    ("global" _ name? exports) /
    ("global" _ name? open "import" _ string _ string close global_type)
    ) close
func = open (
    ("func" _ name? _ func_type locals instrs) /
    ("func" _ name? exports) /
    ("func" _ name? open "import" _ string _ string close func_type)
    ) close

exports_opt = (_ "export" _ string)*
exports = (_ "export" _ string)+

exprs = (_ expr)+
expr = open (
  op /
  (op exprs) /
  ("block" _ name? _ block_type instrs) /
  ("loop"  _ name? _ block_type instrs) /
  ("if"    _ name? _ block_type       open "then" instrs close (open "else" instrs close)?) /
  ("if"    _ name? _ block_type exprs open "then" instrs close (open "else" instrs close)?)
  ) close

instrs = (_ instr)*
instr = open (
  expr /
  op /
  ("block" _ name? _ block_type instrs _ "end" _ name?) /
  ("loop"  _ name? _ block_type instrs _ "end" _ name?) /
  ("if"    _ name? _ block_type instrs _ "end" _ name?) /
  ("if"    _ name? _ block_type instrs _ "else" _ name? instrs "end" _ name? )
  ) close


block_type = ("result" valtypes)*
func_type = ("type" _ var)? params results
global_type = valtype / ("mut" valtype)
table_type = nat _ nat? _ elem_type
memory_type = nat _ nat?

elem_type = "funcref"

"""

cache = """

instr =
  expr /
  ("loop"  _ name? _ block_type instrs _ "end" _ name?) /
  ("if"    _ name? _ block_type instrs _ "end" _ name?) /
  ("if"    _ name? _ block_type instrs _ "else" _ name? instrs "end" _ name? )

exprs = (_ expr)+
expr = open (
  (op exprs) /
  ("if"    _ name? _ block_type       open "then" instrs close (open "else" instrs close)?) /
  ("if"    _ name? _ block_type exprs open "then" instrs close (open "else" instrs close)?)
  ) close


named_block_instr = "block" _ name)? results? instrs _ "end" _ name?) /
"""

GRAMMAR = parsimonious.Grammar(r"""
component = results / params / locals / func_type / op / instrs

instrs = instr instrs_tail*
instrs_tail = (_ instr)
instr = open any_instr close
any_instr =
    folded_instr /
    op /
    block_instr /
    loop_instr

loop_instr = "loop"  (_ name)? loop_tail?
loop_tail = (_ result)? (_ instrs)?

block_instr = "block" (_ name)? block_tail?
block_tail = (_ result)? (_ instrs)?

folded_instr = op _ instrs

op = numeric_op / memory_op / variable_op / parametric_op / control_op

control_op =
    unreachable_op /
    nop_op /
    br_if_op /
    br_table_op /
    br_op /
    return_op /
    call_op /
    call_indirect_op

unreachable_op = "unreachable"
nop_op = "nop"

return_op = "return"

br_if_op = "br_if" _ var
br_table_op = "br_table" _ vars
br_op = "br" _ var

call_op = "call" _ var
call_indirect_op = "call_indirect" _ typeuse

func_type = open "func" _ typeuse close

typeuse = typeuse_direct / typeuse_params_and_results / params / results
typeuse_direct = open "type" _ var close
typeuse_params_and_results = params _ results

parametric_op = "drop" / "select"

variable_op = (local_variable_op / global_variable_op) _ var

global_variable_op = "global.get" / "global.set"
local_variable_op ="local.get" / "local.set" / "local.tee"

memory_op =
    memory_access_op /
    memory_size_op /
    memory_grow_op

memory_size_op = "memory.size"
memory_grow_op = "memory.grow"

memory_access_op = memory_load_op / memory_store_op

memory_store_op = memory_store_float_op / memory_store_integer_op
memory_store_float_op = float_types ".store" memory_arg
memory_store_integer_op = integer_types ".store" (("8" / "16" / "32") memory_arg)?

memory_load_op = memory_load_float_op / memory_load_integer_op
memory_load_float_op = float_types ".load" memory_arg
memory_load_integer_op = integer_types ".load" (("8" / "16" / "32") "_" sign memory_arg)?

memory_arg = (_ offset)? (_ align)?

align = "align=" ("1" / "2" / "4" / "8" / "16" / "32")
offset = "offset=" nat

numeric_op =
    constop /
    testop /
    unop /
    relop /
    binop /
    wrapop /
    extendop /
    truncop /
    convertop /
    demoteop /
    promoteop /
    reinterpretop


reinterpretop =
    (i32 ".reinterpret_" f32) /
    (i64 ".reinterpret_" f64) /
    (f32 ".reinterpret_" i32) /
    (f64 ".reinterpret_" i64)
promoteop = f64 ".promote_" f32
demoteop = f32 ".demote_" f64
convertop = float_types ".convert_" integer_types "_" sign
truncop = integer_types ".trunc_" float_types "_" sign
extendop = i64 ".extend_" i32 "_" sign
wrapop = i32 ".wrap_" i64
unop = integer_unop / float_unop
relop = integer_relop / float_relop
binop = integer_binop / float_binop
testop = integer_types ".eqz"
constop = valtype ".const" _ value

float_unop  = float_types "." float_unop_names
float_binop = float_types "." float_binop_names
float_relop = float_types "." float_relop_names

integer_unop = integer_types "." integer_unop_names
integer_binop = integer_types "." integer_binop_names
integer_relop = integer_types "." integer_relop_names

integer_unop_names =
    "clz" /
    "ctz" /
    "popcnt"
integer_binop_names =
    "add" /
    "sub" /
    "mul" /
    ("div_" sign) /
    ("rem_" sign) /
    "and" /
    "or" /
    "xor" /
    "shl" /
    "shr_s" /
    "shr_u" /
    "rotl" /
    "rotr"
integer_relop_names =
    "eq" /
    "ne" /
    ("lt_" sign) /
    ("gt_" sign) /
    ("le_" sign) /
    ("ge_" sign)
float_unop_names =
    "abs" /
    "neg" /
    "ceil" /
    "floor" /
    "trunc" /
    "nearest" /
    "sqrt"
float_binop_names =
    "add" /
    "sub" /
    "mul" /
    "div" /
    "min" /
    "max" /
    "copysign"
float_relop_names =
    "eq" /
    "ne" /
    "lt" /
    "gt" /
    "le" /
    "ge"

sign = "s" / "u"

params = param params_tail*
params_tail = (_ param)
param = open any_param close
any_param = bare_param / named_param / empty_param

named_param = "param" _ name _ valtype
bare_param  = "param" _        valtypes
empty_param = "param"

results = result results_tail*
results_tail = _ result
result = open any_result close
any_result = declared_result / empty_result
declared_result = "result" _ valtypes
empty_result = "result"

locals = local locals_tail*
locals_tail = (_ local)
local = open any_local close
any_local = bare_local / named_local

named_local = "local" _ name _ valtype
bare_local  = "local" _        valtypes

valtypes = valtype valtypes_tail*
valtypes_tail = _ valtype
valtype = integer_types / float_types

float_types = f32 / f64
integer_types = i32 / i64

i32 = "i32"
i64 = "i64"
f32 = "f32"
f64 = "f64"

vars = var vars_tail*
vars_tail = _ var
var = nat / name
value = int / float

string = double_quote (
    char / newline / tab / escaped_backslash /
    escaped_single_quote / escaped_double_quote /
    escaped_hex_char / escaped_unicode_char
    )* double_quote
name = "$" (
    letter / digit /
    "_" / "." /
    "+" / "-" / "*" / "/" /
    backslash / "^" / "~" / "=" / "<" / ">" /
    "!" / "?" / "@" / "#" / "$" / "%" / "&" /
    "|" / ":" / "'" / "`"
    )+

char = letter / digit
letter = ~"[a-zA-Z]"

newline = "\n"
tab = "\t"
backslash = "\\"

escaped_hex_char = backslash hexdigit hexdigit
escaped_unicode_char = "\\u" hexdigit+

escaped_backslash = "\\\\"

single_quote = "'"
double_quote = "\""

escaped_single_quote = "\\\'"
escaped_double_quote = "\\\""

float = (num "." num? (("e" / "E") num)?) / ("0x" hexnum "." hexnum? (("p" / "P") num)?)
int = nat / ("+" nat) / ("-" nat)
nat = num / ("0x" hexnum)

hexnum = hexdigit+
hexdigit = ~"[0-9a-fA-F]"

open = "(" _?
close = _? ")"
num = digit+
digit = ~"[0-9]"
_ = whitespace
whitespace = whitespace_chars+
whitespace_chars = " " / "\n" / "/t"
""")
