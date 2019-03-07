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

op =
    control_ops /
    parametric_ops /
    variable_ops /
    memory_ops /
    numeric_ops


control_ops =
    "unreachable" /
    "nop" /
    ("br" _ var) /
    ("br_if" _ var) /
    ("br_table" vars) /
    "return" /
    ("call" _ var) /
    ("call_indirect" _ func_type) /

parametric_ops =
    "drop" /
    "select" /

variable_ops =
    ("local.get" _ var) /
    ("local.set" _ var) /
    ("local.tee" _ var) /
    ("global.get" _ var) /
    ("global.set" _ var) /

memory_ops =
    (integer_types ".load" ("8" / "16" / "32")? "_" sign (_ offset)? (_ align)?) /
    (float_types ".load" (_ offset?) (_ align)?) /
    (integer_types ".store" ("8" / "16")? (_ offset)? (_ align)?) /
    (float_types ".store" (_ offset)? (_ align)?) /
    "memory.size" /
    "memory.grow" /

align = "align=" ("1" / "2" / "4" / "8" / "16" / "32")
offset = "offset=" nat

numeric_ops =
    (numeric_const_op _ value) /
    float_ops /
    integer_ops /
    (i32 ".wrap_" i64) /
    (i64 ".extend_" i32 "_" sign) /
    (i32 ".trunc_" float_types "_" sign) /
    (i64 ".trunc_" float_types "_" sign) /
    (float_types ".convert_" integer_types "_" sign) /
    (f32 ".demote_" f64) /
    (f64 ".promote" f32) /
    (i32 ".reinterpret_" f32) /
    (i64 ".reinterpret_" f64) /
    (f32 ".reinterpret_" i32) /
    (f64 ".reinterpret_" i64)


float_ops = float_types "." (float_unop_names / float_binop_names / float_relop_names)
integer_ops = integer_types "." (integer_binop_names / integer_relop_names)

block_type = ("result" valtypes)*
func_type = ("type" _ var)? params results
global_type = valtype / ("mut" valtype)
table_type = nat _ nat? _ elem_type
memory_type = nat _ nat?

elem_type = "funcref"

"""

cache = """

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
integer_relop_names =
    "eqz" /
    "eq" /
    "ne" /
    ("lt_" sign) /
    ("gt_" sign) /
    ("le_" sign) /
    ("ge_" sign)
float_relop_names =
    "eq" /
    "ne" /
    "lt" /
    "gt" /
    "le" /
    "ge"

sign = "s" / "u"

"""

GRAMMAR = parsimonious.Grammar(r"""
component = results / params / locals / op

op = numeric_const_op

numeric_const_op = open valtype ".const" _ value close

params = param params_tail*
params_tail = (_ param)
param = open any_param close
any_param = bare_param / named_param

named_param = "param" _ name _ valtype
bare_param  = "param" _        valtypes

results = result results_tail*
results_tail = _ result
result = open "result" _ valtypes close

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
