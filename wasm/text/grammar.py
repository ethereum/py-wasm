import functools

import parsimonious
from parsimonious import (
    expressions,
)

from wasm.exceptions import (
    ParseError,
)

"""
type = types optional?
types = basic_type / alias_type / container_type / tuple_type / array_type

container_type = container_types optional? arrlist?
container_types = zero_container / non_zero_container
tuple_type = type const_arr optional?
array_type = type dynam_arr optional?

non_zero_container = "{" type next_type* "}"
next_type = "," type

zero_container = "{}"

optional = "?"

basic_type = basic_types optional? arrlist?
basic_types = integer_types / bit_type
bit_type = "bit"

integer_types = base_integer_type bit_size
bit_size = ~"[1-9][0-9]*"
base_integer_type = "uint" / "scalar"

alias_type = alias_types optional? arrlist?
alias_types = bool_type / bytesN_type / bytes_type / byte_type

bytesN_type = bytes_type digits

bool_type = "bool"
bytes_type = "bytes"
byte_type = "byte"

arrlist = dynam_arr / const_arr
dynam_arr = dynam_arr_comp any_arr_comp*
const_arr = const_arr_comp any_arr_comp*

any_arr_comp = (const_arr_comp / dynam_arr_comp)*

dynam_arr_comp = "[]"
const_arr_comp = "[" digits "]"

digits = ~"[1-9][0-9]*"
"""


DONE = """

func:    ( func <name>? <func_type> <local>* <instr>* )
         ( func <name>? ( export <string> ) <...> )                         ;; = (export <string> (func <N>)) (func <name>? <...>)
         ( func <name>? ( import <string> <string> ) <func_type>)           ;; = (import <name>? <string> <string> (func <func_type>))
param:   ( param <val_type>* ) | ( param <name> <val_type> )
result:  ( result <val_type>* )
local:   ( local <val_type>* ) | ( local <name> <val_type> )

global:  ( global <name>? <global_type> <instr>* )
         ( global <name>? ( export <string> ) <...> )                       ;; = (export <string> (global <N>)) (global <name>? <...>)
         ( global <name>? ( import <string> <string> ) <global_type> )      ;; = (import <name>? <string> <string> (global <global_type>))
table:   ( table <name>? <table_type> )
         ( table <name>? ( export <string> ) <...> )                        ;; = (export <string> (table <N>)) (table <name>? <...>)
         ( table <name>? ( import <string> <string> ) <table_type> )        ;; = (import <name>? <string> <string> (table <table_type>))
         ( table <name>? ( export <string> )* <elem_type> ( elem <var>* ) ) ;; = (table <name>? ( export <string> )* <size> <size> <elem_type>) (elem (i32.const 0) <var>*)
elem:    ( elem <var>? (offset <instr>* ) <var>* )
         ( elem <var>? <expr> <var>* )                                      ;; = (elem <var>? (offset <expr>) <var>*)
memory:  ( memory <name>? <memory_type> )
         ( memory <name>? ( export <string> ) <...> )                       ;; = (export <string> (memory <N>))+ (memory <name>? <...>)
         ( memory <name>? ( import <string> <string> ) <memory_type> )      ;; = (import <name>? <string> <string> (memory <memory_type>))
         ( memory <name>? ( export <string> )* ( data <string>* ) )         ;; = (memory <name>? ( export <string> )* <size> <size>) (data (i32.const 0) <string>*)
data:    ( data <var>? ( offset <instr>* ) <string>* )
         ( data <var>? <expr> <string>* )                                   ;; = (data <var>? (offset <expr>) <string>*)

start:   ( start <var> )

typedef: ( type <name>? ( func <param>* <result>* ) )

import:  ( import <string> <string> <imkind> )
imkind:  ( func <name>? <func_type> )
         ( global <name>? <global_type> )
         ( table <name>? <table_type> )
         ( memory <name>? <memory_type> )
export:  ( export <string> <exkind> )
exkind:  ( func <var> )
         ( global <var> )
         ( table <var> )
         ( memory <var> )

module:  ( module <name>? <typedef>* <func>* <import>* <export>* <table>? <memory>? <global>* <elem>* <data>* <start>? )
         <typedef>* <func>* <import>* <export>* <table>? <memory>? <global>* <elem>* <data>* <start>?  ;; =
         ( module <typedef>* <func>* <import>* <export>* <table>? <memory>? <global>* <elem>* <data>* <start>? )
"""


grammar = parsimonious.Grammar(r"""
import = "import" _ string _ string _ imkind
export = "export" _ string _ exkind

imkind =
    ("func _ name? _ func_type) /
    ("global _ name? _ global_type) /
    ("table _ name? _ table_type) /
    ("memory _ name? _ memory_type)
exkind =
    ("func _ var) /
    ("global _ var) /
    ("table _ var) /
    ("memory _ var)

func =
    ("func" _ name? _ func_type _ local* _ instr*) /
    ("func" _ name? _ ("export" _ string) <...> )                         ;; = (export <string> (func <N>)) (func <name>? <...>)
    ("func" name? ("import" <string> <string> ) <func_type>)           ;; = (import <name>? <string> <string> (func <func_type>))

expr =
  op /
  (op _ expr+) /
  ("block" _ name? _ block_type _ instr*) /
  ("loop" _ name? _ block_type _ instr*) /
  ("if" _ name? _ block_type _ ("then" _ instr*) _ ("else" _ instr*)?) /
  ("if" _ name? _ block_type _ expr+ _ ("then" _ instr*) ("else" instr*)?)

instr =
  expr /
  op /
  ("block" _ name? _ block_type _ instr* _ "end" _ name?) /
  ("loop" _ name? _ block_type _ instr* _ "end" _ name?) /
  ("if" _ name? _ block_type _ instr* _ "end" _ name?) /
  ("if" _ name? _ block_type _ instr* "else" name? instr* "end" name? )

op =
  "unreachable" /
  nop" /
  ("br" _ var) /
  ("br_if _ var) /
  ("br_table _ var+) /
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

val_type = integer_types / float_types

sign = "s" / "u"

float_types = f32 / f64
integer_types = i32 / i64

i32 = "i32"
i64 = "i64"
f32 = "f32"
f64 = "f64"

elem_type = "funcref"
block_type = ("result" (_ val_type)*)*
func_type:   ("type" _ var)? param* result*
global_type: val_type | ("mut" val_type)
table_type:  nat nat? elem_type
memory_type: nat nat?

param = ("param" (_ val_type)*) | ("param" _ name _ val_type)
result = "result" (_ val_type)*
local = ("local" (_ val_type)*) | ("local" _ name _ val_type)

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


align = "align=" ("1" / "2" / "4" / "8" / "16" / "32")
offset: offset=<nat>


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
