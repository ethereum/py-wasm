import functools

import parsimonious
from parsimonious import (
    expressions,
)

from wasm.exceptions import (
    ParseError,
)

grammar = parsimonious.Grammar(r"""
script = (_ cmd)*

cmd =
  module /
  ("register" string name?) /
  action /
  assertion /
  meta

assertion:
  ("assert_return"                _ action exprs) /
  ("assert_return_canonical_nan"  _ action) /
  ("assert_return_arithmetic_nan" _ action) /
  ("assert_trap"                  _ action _ string) /
  ("assert_malformed"             _ module _ string) /
  ("assert_invalid"               _ module _ string) /
  ("assert_unlinkable"            _ module _ string) /
  ("assert_trap"                  _ module _ string) /

action:
  ("invoke" _ name? _ string exprs) /
  ("get" _ name? _ string)

meta =
  ("script" _ name? script) /
  ("input"  _ name? string) /
  ("output" _ name? string?)


module =
    ("module" _ name? _ sections) /
    (                 _ sections) /
    ("module"         _ sections /
    ("module" _ name? _ "binary" strings) /
    ("module" _ name? _ "quote" strings)

secs = typedef* _ func* _ import* _ export* _ table? _ memory? _ global* _ elem* _ data* _ start?

start = "start" var

typedef = "type" name? "func" params results

import = "import" _ string _ string _ imkind
export = "export" _ string _ exkind

imkind =
    ("func" _ name? _ func_type) /
    ("global" _ name? _ global_type) /
    ("table" _ name? _ table_type) /
    ("memory" _ name? _ memory_type)
exkind =
    ("func" _ var) /
    ("global" _ var) /
    ("table" _ var) /
    ("memory" _ var)

data =
    ("data" _ var? _ offset instrs strings) /
    ("data" _ var? _ expr strings)
memory =
    ("memory" _ name? memory_type) /
    ("memory" _ name? exports) /
    ("memory" _ name? _ ("import" _ string _ string) _ memory_type) /
    ("memory" _ name? exports_opt _ ("data" strings))
elem =
    ("elem" _ var? _ offset instrs vars) /
    ("elem" _ var? _ expr vars)
table =
    ("table" _ name? _ table_type) /
    ("table" _ name? exports) /
    ("table" _ name? _ ("import" string _ string) _ table_type) /
    ("table" _ name? exports_opt _ elem_type _ ("elem" vars))
global =
    ("global" _ name? _ global_type instrs) /
    ("global" _ name? exports) /
    ("global" _ name? _ ("import" _ string _ string) global_type)
func =
    ("func" _ name? _ func_type locals instrs) /
    ("func" _ name? exports) /
    ("func" _ name? _ ("import" _ string _ string) _ func_type)

exports_opt = (_ "export" _ string)*
exports = (_ "export" _ string)+

expr =
  op /
  (op _ expr+) /
  ("block" _ name? _ block_type instrs) /
  ("loop" _ name? _ block_type instrs) /
  ("if" _ name? _ block_type _ ("then" instrs)) _ ("else" instrs)?) /
  ("if" _ name? _ block_type _ expr+ _ ("then" _ instr*) ("else" instrs)?)

instrs = (_ instr)*
instr =
  expr /
  op /
  ("block" _ name? _ block_type instrs _ "end" _ name?) /
  ("loop" _ name? _ block_type instrs _ "end" _ name?) /
  ("if" _ name? _ block_type instrs _ "end" _ name?) /
  ("if" _ name? _ block_type instrs _ "else" _ name? instrs "end" _ name? )

elem_type = "funcref"
block_type = ("result" valtypes)*
func_type:   ("type" _ var)? params results
global_type: val_type | ("mut" val_type)
table_type:  nat _ nat? _ elem_type
memory_type: nat _ nat?

params = (_ param)*
param = ("param" valtypes) | ("param" _ name _ val_type)
results = (_ result)*
result = "result" valtypes
locals = (_ local)*
local = ("local" valtypes) | ("local" _ name _ val_type)

op =
  "unreachable" /
  "nop" /
  ("br" _ var) /
  ("br_if _ var) /
  ("br_table vars) /
  "return" /
  ("call" _ var) /
  ("call_indirect" _ func_type) /
  "drop" /
  "select" /
  ("local.get" _ var) /
  ("local.set" _ var) /
  ("local.tee" _ var) /
  ("global.get" _ var) /
  ("global.set" _ var) /
  (integer_types ".load" ("8" / "16" / "32")? "_" sign (_ offset)? (_ align)?) /
  (float_types ".load" (_ offset?) (_ align)?) /
  (integer_types ".store" ("8" / "16")? (_ offset)? (_ align)?) /
  (float_types ".store" (_ offset)? (_ align)?) /
  "memory.size" /
  "memory.grow" /
  (numeric_const_op _ value) /
  numeric_op

numeric_op =
    float_ops /
    integer_ops /
    i32 ".wrap_" i64 /
    i32 ".trunc_" float_types "_" sign /
    i64 ".extend_" i32 "_" sign /
    i64 ".trunc_" float_types "_" sign /
    float_types ".convert_" integer_types "_" sign /
    f32 ".demote_" f64 /
    f64 ".promote" f32 /
    i32 ".reinterpret_" f32 /
    i64 ".reinterpret_" f64 /
    f32 ".reinterpret_" i32 /
    f64 ".reinterpret_" i64


float_ops = float_types "." (float_unop_names | float_binop_names | float_relop_names)
integer_ops = integer_types "." (integer_binop_names | integer_relop_names)
numeric_const_op = valtype ".const"

integer_binop_names =
    "add" /
    "sub" /
    "mul" /
    "div_" sign /
    "rem_" sign /
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
    "lt_" sign /
    "gt_" sign /
    "le_" sign /
    "ge_" sign
float_relop_names =
    "eq" /
    "ne" /
    "lt" /
    "gt" /
    "le" /
    "ge"


align = "align=" ("1" / "2" / "4" / "8" / "16" / "32")
offset = "offset=" nat

val_types = (_ val_type)*
val_type = integer_types / float_types

sign = "s" / "u"

float_types = f32 / f64
integer_types = i32 / i64

i32 = "i32"
i64 = "i64"
f32 = "f32"
f64 = "f64"

vars = (_ var)+
var = nat / name
value = int / float

strings = (_ string)*
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

char = letter | digit
letter = ~"[a-zA-Z]"

newline = "\n"
tab = "\t"
backslash = "\\"

escaped_hex_char = backslash hexdigit hexdigit
escaped_unicode_char = "\u" hexdigit+

escaped_backslash "\\\\"

single_quote = "'"
double_quote = "\""

escaped_single_quote = "\\\'"
escaped_double_quote = "\\\""

float = num "." num? (("e" / "E") num)? / "0x" hexnum "." hexnum? (("p" / "P") num)?
int = nat / "+" nat / "-" nat
nat = num / "0x" hexnum

hexnum = hexdigit (_? hexdigit)*
hexdigit = ~"[0-9a-fA-F]"

num = digit (_? digit)*
digit = ~"[0-9]"
""")


class NodeVisitor(parsimonious.NodeVisitor):
    """
    Parsimonious node visitor which performs both parsing of type strings and
    post-processing of parse trees.  Parsing operations are cached.
    """
    grammar = grammar

    ############
    def visit_digits(self, node, visited_children):
        return int(node.text)

    def generic_visit(self, node, visited_children):
        if isinstance(node.expr, expressions.OneOf):
            # Unwrap value chosen from alternatives
            return visited_children[0]

        if isinstance(node.expr, expressions.Optional):
            # Unwrap optional value or return `None`
            if len(visited_children) != 0:
                return visited_children[0]

            return None

        return tuple(visited_children)

    @functools.lru_cache(maxsize=None)
    def parse(self, type_str):
        """
        Parses a type string into an appropriate instance of
        :class:`~eth_abi.grammar.ABIType`.  If a type string cannot be parsed,
        throws :class:`~eth_abi.exceptions.ParseError`.

        :param type_str: The type string to be parsed.
        :returns: An instance of :class:`~eth_abi.grammar.ABIType` containing
            information about the parsed type string.
        """
        if not isinstance(type_str, str):
            raise TypeError('Can only parse string values: got {}'.format(type(type_str)))

        try:
            return super().parse(type_str)
        except parsimonious.ParseError as e:
            raise ParseError(e.text, e.pos, e.expr)


visitor = NodeVisitor()


parse = visitor.parse
