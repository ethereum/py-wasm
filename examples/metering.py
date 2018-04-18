#!/usr/bin/env python

import sys
sys.path.append('..')

from pyWebAssembly import *




#cost of each intstruction
instr_cost = {
'unreachable':1,'nop':1,
'block':1, 'loop':1, 'if':1, 'else':1, 'end':1,
'br':1, 'br_if':1, 'br_table':1,
'return':1, 'call':1, 'call_indirect':1,

'drop':1,'select':1,

'get_local':1, 'set_local':1, 'tee_local':1, 'get_global':1, 'set_global':1,

'i32.load':1, 'i64.load':1, 'f32.load':1, 'f64.load':1, 'i32.load8_s':1, 'i32.load8_u':1, 'i32.load16_s':1, 'i32.load16_u':1, 'i64.load8_s':1, 'i64.load8_u':1, 'i64.load16_s':1, 'i64.load16_u':1, 'i64.load32_s':1, 'i64.load32_u':1, 'i32.store':1, 'i64.store':1, 'f32.store':1, 'f64.store':1, 'i32.store8':1, 'i32.store16':1, 'i64.store8':1, 'i64.store16':1, 'i64.store32':1,
'current_memory':1,'grow_memory':1,

'i32.const':1, 'i64.const':1, 'f32.const':1, 'f64.const':1,

'i32.eqz':1, 'i32.eq':1, 'i32.ne':1, 'i32.lt_s':1, 'i32.lt_u':1, 'i32.gt_s':1, 'i32.gt_u':1, 'i32.le_s':1, 'i32.le_u':1, 'i32.ge_s':1, 'i32.ge_u':1,

'i64.eqz':1, 'i64.eq':1, 'i64.ne':1, 'i64.lt_s':1, 'i64.lt_u':1, 'i64.gt_s':1, 'i64.gt_u':1, 'i64.le_s':1, 'i64.le_u':1, 'i64.ge_s':1, 'i64.ge_u':1,

'f32.eq':1, 'f32.ne':1, 'f32.lt':1, 'f32.gt':1, 'f32.le':1, 'f32.ge':1,

'f64.eq':1, 'f64.ne':1, 'f64.lt':1, 'f64.gt':1, 'f64.le':1, 'f64.ge':1,

'i32.clz':1, 'i32.ctz':1, 'i32.popcnt':1, 'i32.add':1, 'i32.sub':1, 'i32.mul':1, 'i32.div_s':1, 'i32.div_u':1, 'i32.rem_s':1, 'i32.rem_u':1, 'i32.and':1, 'i32.or':1, 'i32.xor':1, 'i32.shl':1, 'i32.shr_s':1, 'i32.shr_u':1, 'i32.rotl':1, 'i32.rotr':1,

'i64.clz':1, 'i64.ctz':1, 'i64.popcnt':1, 'i64.add':1, 'i64.sub':1, 'i64.mul':1, 'i64.div_s':1, 'i64.div_u':1, 'i64.rem_s':1, 'i64.rem_u':1, 'i64.and':1, 'i64.or':1, 'i64.xor':1, 'i64.shl':1, 'i64.shr_s':1, 'i64.shr_u':1, 'i64.rotl':1, 'i64.rotr':1,

'f32.abs':1, 'f32.neg':1, 'f32.ceil':1, 'f32.floor':1, 'f32.trunc':1, 'f32.nearest':1, 'f32.sqrt':1, 'f32.add':1, 'f32.sub':1, 'f32.mul':1, 'f32.div':1, 'f32.min':1, 'f32.max':1, 'f32.copysign':1, 'f64.abs':1,

'f64.neg':1, 'f32.min':1, 'f32.max':1, 'f32.copysign':1, 'f64.abs':1, 'f64.neg':1, 'f64.ceil':1, 'f64.floor':1, 'f64.trunc':1, 'f64.nearest':1, 'f64.sqrt':1, 'f64.add':1, 'f64.sub':1, 'f64.mul':1, 'f64.div':1, 'f64.min':1, 'f64.max':1, 'f64.copysign':1,

'i32.wrap/i64':1, 'i32.trunc_s/f32':1, 'i32.trunc_u/f32':1, 'i32.trunc_s/f64':1, 'i32.trunc_u/f64':1, 'i64.extend_s/i32':1, 'i64.extend_u/i32':1, 'i64.trunc_s/f32':1, 'i64.trunc_u/f32':1, 'i64.trunc_s/f64':1, 'i64.trunc_u/f64':1, 'f32.convert_s/i32':1, 'f32.convert_u/i32':1, 'f32.convert_s/i64':1, 'f32.convert_u/i64':1, 'f32.demote/f64':1, 'f64.convert_s/i32':1, 'f64.convert_u/i32':1, 'f64.convert_s/i64':1, 'f64.convert_u/i64':1, 'f64.promote/f32':1, 'i32.reinterpret/f32':1, 'i64.reinterpret/f64':1, 'f32.reinterpret/i32':1, 'f64.reinterpret/i64':1
}




def inject_metering_calls_to_each_function(mod):
  for f in mod["funcs"]:
    #for e in f["body"]:
    f["body"]=inject_metering_expr(f["body"],len(mod["funcs"])) #len(mod["funcs"]) is idx of metering func in wasm



#THIS IS THE IMPORTANT FUNCTION; RECURSIVELY INJECTS METERING CALLS
def inject_metering_expr(expr,meteringFuncIdx):
  #inject to beginning of list
  #expr=[("i32.const",0),("call",meteringFuncIdx)]+expr
  cost=0
  #cost_instr=expr[0]
  idx_to_inject=0
  i=0
  #print(expr)
  while i<len(expr):
    #print(i,expr[i][0],expr[i])
    cost+=instr_cost[expr[i][0]]
    if expr[i][0] in {"block","if","loop","br","br_if","br_table"}:
      #cost_instr[1]=cost
      #inject
      if cost !=0:
        #print("injecting  i:",i,"idx_to_inject",idx_to_inject)
        expr=expr[:idx_to_inject]+[("i32.const",cost),("call",meteringFuncIdx)]+expr[idx_to_inject:]
        idx_to_inject=i+3
        cost=0
        i+=2
      #recurse on nested exprs
      if expr[i][0] in {"block","if","loop"}:
        expr[i][2][:]=inject_metering_expr(expr[i][2],meteringFuncIdx)
      #if not end, inject another
      #if i<len(expr)-1:
      #  cost=0
      #  expr=expr[:i+1]+[("i32.const",0),("call",meteringFuncIdx)]+expr[i+1:]
      #  cost_instr=expr[i]
    i+=1
  if cost !=0:
    expr=expr[:idx_to_inject]+[("i32.const",cost),("call",meteringFuncIdx)]+expr[idx_to_inject:]
  return expr



def inject_helper_functions(mod):
  #inject globals for cycles_remaining
  global_idx_cycles = len(mod["globals"])
  mod["globals"]+=[{'type': ('var', 'i32'), 'init': [('i32.const', 0)]}, {'type': ('var', 'i32'), 'init': [('i32.const', 0)]}, {'type': ('var', 'i32'), 'init': [('i32.const', 0)]}, {'type': ('var', 'i32'), 'init': [('i32.const', 0)]}]
  #inject function to perform metering
  mod["types"]+=[(['i32'],[])]
  mod["funcs"]+=[{'type': len(mod["types"])-1, 'locals': [['i32']], 'body': [('get_global', 0+global_idx_cycles), ('set_local', 1), ('get_global', 0+global_idx_cycles), ('get_local', 0), ('i32.sub',), ('set_global', 0+global_idx_cycles), ('get_global', 0+global_idx_cycles), ('get_local', 1), ('i32.gt_u',), ('if', None, [('get_global', 1+global_idx_cycles), ('set_local', 1), ('get_global', 1+global_idx_cycles), ('i32.const', 1), ('i32.sub',), ('set_global', 1+global_idx_cycles), ('get_global', 1+global_idx_cycles), ('get_local', 1), ('i32.gt_u',), ('if', None, [('get_global', 2+global_idx_cycles), ('set_local', 1), ('get_global', 2+global_idx_cycles), ('i32.const', 1), ('i32.sub',), ('set_global', 2+global_idx_cycles), ('get_global', 2+global_idx_cycles), ('get_local', 1), ('i32.gt_u',), ('if', None, [('get_global', 3+global_idx_cycles), ('set_local', 1), ('get_global', 3+global_idx_cycles), ('i32.const', 1), ('i32.sub',), ('set_global', 3+global_idx_cycles), ('get_global', 3+global_idx_cycles), ('get_local', 1), ('i32.gt_u',), ('if', None, [('unreachable',)])])])])]}]
  """
  (func (;1;) (type 1) (param i32)
    (local i32)
    get_global 0
    set_local 1
    get_global 0
    get_local 0
    i32.sub
    set_global 0
    get_global 0
    get_local 1
    i32.gt_u
    if  ;; label = @1
      get_global 1
      set_local 1
      get_global 1
      i32.const 1
      i32.sub
      set_global 1
      get_global 1
      get_local 1
      i32.gt_u
      if  ;; label = @2
        get_global 2
        set_local 1
        get_global 2
        i32.const 1
        i32.sub
        set_global 2
        get_global 2
        get_local 1
        i32.gt_u
        if  ;; label = @3
          get_global 3
          set_local 1
          get_global 3
          i32.const 1
          i32.sub
          set_global 3
          get_global 3
          get_local 1
          i32.gt_u
          if  ;; label = @4
            unreachable
          end
        end
      end
    end)
  """
  #inject function to get cycles remaining
  mod["types"]+=[(['i32'], ['i32'])]
  mod["funcs"]+=[{'type': len(mod["types"])-1, 'locals': [], 'body': [('get_local', 0), ('i32.const', 0), ('i32.eq',), ('if', 'i32', [('get_global', 0+global_idx_cycles)], [('get_local', 0), ('i32.const', 1), ('i32.eq',), ('if', 'i32', [('get_global', 1+global_idx_cycles)], [('get_local', 0), ('i32.const', 2), ('i32.eq',), ('if', 'i32', [('get_global', 2+global_idx_cycles)], [('get_global', 3+global_idx_cycles)])])])]}]
  mod["exports"]+=[{'name': 'get_max_cycles', 'desc': {'func': len(mod["funcs"])-1}}]
  """
  (func (;2;) (type 2) (param i32) (result i32)
    get_local 0
    i32.const 0
    i32.eq
    if (result i32)  ;; label = @1
      get_global 0
    else
      get_local 0
      i32.const 1
      i32.eq
      if (result i32)  ;; label = @2
        get_global 1
      else
        get_local 0
        i32.const 2
        i32.eq
        if (result i32)  ;; label = @3
          get_global 2
        else
          get_global 3
        end
      end
    end)
  """
  #inject function to set max_cycles
  mod["types"]+=[(['i32','i32'],[])]
  mod["funcs"]+=[{'type': len(mod["types"])-1, 'locals': [], 'body': [('get_local', 0), ('i32.const', 0), ('i32.eq',), ('if', None, [('get_local', 1), ('set_global', 0+global_idx_cycles)], [('get_local', 0), ('i32.const', 1), ('i32.eq',), ('if', None, [('get_local', 1), ('set_global', 1+global_idx_cycles)], [('get_local', 0), ('i32.const', 2), ('i32.eq',), ('if', None, [('get_local', 1), ('set_global', 2+global_idx_cycles)], [('get_local', 1), ('set_global', 3+global_idx_cycles)])])])]}]
  mod["exports"]+=[{'name': 'set_max_cycles', 'desc': {'func': len(mod["funcs"])-1}}]
  """
  (func (;3;) (type 3) (param i32 i32)
    get_local 0
    i32.const 0
    i32.eq
    if  ;; label = @1
      get_local 1
      set_global 0
    else
      get_local 0
      i32.const 1
      i32.eq
      if  ;; label = @2
        get_local 1
        set_global 1
      else
        get_local 0
        i32.const 2
        i32.eq
        if  ;; label = @3
          get_local 1
          set_global 2
        else
          get_local 1
          set_global 3
        end
      end
    end)
  """
  #inject function to get num chunks for max_cycles
  mod["types"]+=[([],['i32'])]
  mod["funcs"]+=[{'type': len(mod["types"])-1, 'locals': [], 'body': [('i32.const', 4)]}]
  mod["exports"]+=[{'name': 'get_num_max_cycles_chunks', 'desc': {'func': len(mod["funcs"])-1}}]
  """
  (func (;4;) (type 4) (result i32)
    i32.const 4)
  """
  #print(mod["types"])
  #print(mod["funcs"])
  #print(mod["exports"])





def tests(mod):
  #print_tree(mod)
  #print_sections(mod)
  print_tree(mod["funcs"])
  #print_sections(mod)
  #test metering injection to each func
  for f in mod["funcs"]:
    #print("\n")
    #pretty_print(f["body"])
    #print(f["body"])
    #print_tree_expr(f["body"])
    f["body"]=inject_metering_expr(f["body"],1000)
    #print()
    #print_tree_expr(f["body"])




def parse_wasm_and_inject_and_generate(filename):
  with open(filename, 'rb') as f:
    wasm = memoryview(f.read())
    mod = spec_module(wasm)
    inject_metering_calls_to_each_function(mod)
    #must inject above metering calls before injecting helper functions
    inject_helper_functions(mod)
    spec_module_inv_to_file(mod,filename.split('.')[0]+"_metered.wasm")


if __name__ == "__main__":
  import sys
  if len(sys.argv)!=2:
    print("Argument should be <filename>.wasm")
  else:
    parse_wasm_and_inject_and_generate(sys.argv[1])
