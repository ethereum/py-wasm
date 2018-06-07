"""

This file runs Wasm tests. The official Wasm test suite provides .wast files with extra opcodes such as `assert_return`. Pywebassembly does not yet parse the the text .wast format, so we use wabt's wast2json to convert each <test>.wast to <test>.json and corresponding <test>.0.wasm, <test>.1.wasm, ... . This python script parses the <test>.json files and executes the tests. Currently, all `assert_return` tests pass (except for floating-point which are not yet implemented in pywebassembly).



To prepare and run the tests:

#get latest pywebassembly
git clone https://github.com/poemm/pywebassembly.git

#compile wabt's tool wast2json
git clone https://github.com/WebAssembly/wabt.git
cd wabt
mkdir BUILD && cd BUILD
cmake ..
make
cd ../..

#get official tests
git https://github.com/WebAssembly/spec.git

#convert official tests to json and wasm files
cd pywebassembly/tests
cp ../../spec/test/core/*.wast .
#for each <test>.wast, execute: ../../wabt/BUILD/wast2json <test>.wast -o <test>.json
for filename in $(find *.wast 2> /dev/null); do
  ../../wabt/BUILD/wast2json $filename "-o" $filename".json"
done

#execute this file on any <test>.json test file
python3 spec_tests.py address.json
#or execute this file on all .json test files
python3 spec_tests.py



TODO:
support extra opcodes:
  assert_return_canonical_nan
  assert_return_arithmetic_nan
  assert_trap
  assert_malformed
  assert_invalid
  assert_unlinkable

"""

import pywebassembly
import json


verbose = 0




###################################################################
# module "spectest" with host functions which are imported by tests
###################################################################

def instantiate_spectest_module(store,modules,registered_modules):
  def spectest__print_i32(store,arg):
    if verbose>1: print(arg)
    return store,[]
  def spectest__print_i64(store,arg):
    if verbose>1: print(arg)
    return store,[]
  def spectest__print_f32(store,arg):
    if verbose>1: print(arg)
    return store,[]
  def spectest__print_f64(store,arg):
    if verbose>1: print(arg)
    return store,[]
  def spectest__print_i32_f32(store,arg):
    if verbose>1: print(arg)
    return store,[]
  def spectest__print_f64_f64(store,arg):
    if verbose>1: print(arg)
    return store,[]
  def spectest__print(store,arg):
    if verbose>1: print(arg)
    return store,[]
  pywebassembly.alloc_func(store, [["i32"],[]], spectest__print_i32)
  pywebassembly.alloc_func(store, [["i64"],[]], spectest__print_i64)
  pywebassembly.alloc_func(store, [["f32"],[]], spectest__print_f32)
  pywebassembly.alloc_func(store, [["f64"],[]], spectest__print_f64)
  pywebassembly.alloc_func(store, [["i32","f32"],[]], spectest__print_i32_f32)
  pywebassembly.alloc_func(store, [["f64","f64"],[]], spectest__print_f64_f64)
  pywebassembly.alloc_func(store, [[],[]], spectest__print)
  pywebassembly.alloc_mem(store, {"min":1,"max":2})	#min:1,max:2 required by import.wast:
  pywebassembly.alloc_global(store, ["const", "i32"], 666)	#666 required by import.wast
  pywebassembly.alloc_global(store, ["const", "f32"], 0.0)
  pywebassembly.alloc_global(store, ["const", "f64"], 0.0)
  pywebassembly.alloc_table(store, [{"min":10,"max":20}, "anyfunc"])  #max was 30, changed to 20 for import.wast
  modules["spectest"] = {"types":[[["i32"],[]],
                                  [["i64"],[]],
                                  [["i32"],[]],
                                  [["f64"],[]],
                                  [["i32","f32"],[]],
                                  [["f64","f64"],[]],
                                  [[],[]],
                                 ],
                         "funcaddrs":[0,1,2,3,4,5,6],
                         "tableaddrs":[0],
                         "memaddrs":[0],
                         "globaladdrs":[0,1,2],
                         "exports":[{"name":"print_i32","value":["func",0]},
                                    {"name":"print_i64","value":["func",1]},
                                    {"name":"print_f32","value":["func",2]},
                                    {"name":"print_f64","value":["func",3]},
                                    {"name":"print_i32_f32","value":["func",4]},
                                    {"name":"print_f64_f64","value":["func",5]},
                                    {"name":"print","value":["func",6]},
                                    {"name":"memory","value":["mem",0]},
                                    {"name":"global_i32","value":["global",0]},
                                    {"name":"global_f32","value":["global",1]},
                                    {"name":"global_f64","value":["global",2]},
                                    {"name":"table","value":["table",0]}
                                   ]
                        }




######################################################
# Tests require instantiating modules from .wasm files
######################################################

def instantiate_module_from_wasm_file(filename,store,registered_modules):
  if verbose>2: print("instantiate_module_from_wasm_file(",filename,")")
  if filename[-5:]!=".wasm":
    if verbose>1: print("we don't yet support .wast or .wat text format files")
    return store,None
  moduleinst = None
  with open(filename, 'rb') as f:
    #memoryview doesn't make copy, bytearray may require copy
    wasmbytes = memoryview(f.read())
    module = pywebassembly.decode_module(wasmbytes)
    #imports preparation
    externvalstar = []
    for import_ in module["imports"]:
      if import_["module"] not in registered_modules: return -1,-1
      importmoduleinst = registered_modules[import_["module"]]
      externval = None
      for export in importmoduleinst["exports"]:
        if export["name"] == import_["name"]:
          externval = export["value"]
      if externval == None: return -1,-1
      if externval[0] != import_["desc"][0]: return -1,-1
      externvalstar += [externval]
    #print("store",store)
    #print("module",module)
    #print("externvalstar",externvalstar)
    store,moduleinst = pywebassembly.instantiate_module(store,module,externvalstar)
    #print("moduleinst",moduleinst)
    #print(store["mems"][0]["data"])
    if moduleinst=="error":
      return store,None
  return store,moduleinst




###################################################
# extra test opcodes, see list here: https://github.com/WebAssembly/spec/blob/master/interpreter/README.md#scripts
# some assert opcodes not yet implemented, only assert_return is implemented
# we plan to keep the following function structure once we support the text format <test>.wast
###################################################


# module opcode

def test_opcode_module(test,store,modules,registered_modules):
  if verbose>2: print("test_opcode_module()")
  moduleinst=None
  if "filename" in test:
    store,moduleinst = instantiate_module_from_wasm_file(test["filename"],store,registered_modules)
    if moduleinst and "name" in test:
      modules[test["name"]] = moduleinst
  if verbose>1 and moduleinst==None: print("could not instantiate")
  #print("moduleinst",moduleinst)
  return store,moduleinst


# register opcode

def test_opcode_register(test,store,modules,registered_modules,moduleinst):
  if "name" in test:
    registered_modules[test["as"]] = modules[test["name"]]
  else:
    registered_modules[test["as"]] = moduleinst


#assertion opcodes  `assert_<blah>`

def test_opcode_assertion(test,store,modules,registered_modules,moduleinst):
  if "filename" in test and test["type"]=="assert_return": #second part temporary
    store,moduleinst = test_opcode_module(test,store,modules,registered_modules)
  ret = None
  if test["type"] == "assert_return":
    ret = test_opcode_assert_return(test,store,modules,registered_modules,moduleinst)
  elif test["type"] == "assert_return_canonical_nan":
    ret = test_opcode_assert_return_canonical_nan()
  elif test["type"] == "assert_return_arithmetic_nan":
    ret = test_opcode_assert_return_arithmetic_nan()
  elif test["type"] == "assert_trap":
    ret = test_opcode_assert_trap()
  elif test["type"] == "assert_malformed":
    ret = test_opcode_assert_malformed()
  elif test["type"] == "assert_invalid":
    ret = test_opcode_assert_invalid()
  elif test["type"] == "assert_unlinkable":
    ret = test_opcode_assert_unlinkable()
  return ret

def test_opcode_assert_return(test,store,modules,registered_modules,moduleinst):
  if verbose>1: print("test_opcode_assert_return")
  ret = test_opcode_action(test,store,modules,registered_modules,moduleinst)
  if verbose>2: print("results:",ret)
  if ret == "trap":
    if verbose>1: print("FAILURE trap")
    return "failure"
  #print("ret",ret)
  #print("test[\"expected\"]",test["expected"])
  if len(ret) != len(test["expected"]):
    if verbose>1: print("FAILURE different number of expected and returned values")
    return "failure"
  if len(ret)==0 and len(test["expected"]) == 0:
    return "success"
  for i in range(len(ret)):
    if verbose>1: print("expected: ",int(test["expected"][i]["value"]),"   actual: ",ret[i])
    if ret[i] != int(test["expected"][i]["value"]): #TODO: handle floats too
      return "failure"
  return "success"

def test_opcode_assert_return_canonical_nan():
  return "failure"

def test_opcode_assert_return_arithmetic_nan():
  return "failure"

def test_opcode_assert_trap():
  return "failure"

def test_opcode_assert_malformed():
  return "failure"

def test_opcode_assert_invalid():
  return "failure"

def test_opcode_assert_unlinkable():
  return "failure"


# action opcodes `get` and `invoke`

def test_opcode_action(test,store,modules,registered_modules,moduleinst):
  if test["action"]["type"] == "invoke":
    return test_opcode_action_invoke(test,store,modules,registered_modules,moduleinst)
  elif test["action"]["type"] == "get":
    return test_opcode_action_get(test,store,modules,registered_modules,moduleinst)

def test_opcode_action_invoke(test,store,modules,registered_modules,moduleinst):
  if verbose>1: print(test["action"]["field"])
  if "module" in test["action"]:
    moduleinst = modules[test["action"]["module"]]
  #print("moduleinst",moduleinst)
  #get function name, which could include unicode bytes like \u001b which must be converted to unicode string
  funcname = test["action"]["field"]
  #print("funcname",funcname)
  funcname_with_codepoints_translated = ""
  idx=0
  utf8_bytes = bytearray()
  for c in funcname:
    utf8_bytes += bytearray([ord(c)])
  utf8_bytes = pywebassembly.spec_binary_uN_inv(len(funcname),32) + utf8_bytes
  _,funcname = pywebassembly.spec_binary_name(utf8_bytes,0)
  #print("funcname",funcname)
  #get function address
  funcaddr = None
  #print(moduleinst["exports"])
  for export in moduleinst["exports"]:
    #print("export[\"name\"]",export["name"])
    if export["name"] == funcname:
      funcaddr = export["value"][1]
  if verbose>2: print("funcaddr",funcaddr)
  #print("funcaddr",funcaddr)
  #funcbody = store["funcs"][funcaddr]["code"]["body"]
  #print(pywebassembly.print_tree_expr(funcbody))
  #get args
  args = []
  float_flag = 0
  for idx in range(len(test["action"]["args"])):
    type_ = test["action"]["args"][idx]["type"]
    value = test["action"]["args"][idx]["value"]
    args+=[ [type_+".const",value] ]
    if type_ in {"f32","f64"}:
      float_flag = 1 #this is a hack to avoid floating point until implemented
      if verbose>1: print("found float arg so skipping")
  #invoke func
  ret = []
  if not float_flag:
    _,ret = pywebassembly.invoke_func(store,funcaddr,args)
  #else:
  #  num_tests_tried-=1
  return ret

def test_opcode_action_get(test,store,modules,registered_modules,moduleinst):
  if "module" in test["action"]:
    moduleinst = modules[test["action"]["module"]]
  exports = moduleinst["exports"]
  #this is naive, since test["expected"] is a list, should iterate over each one, but maybe OK since there is only one test["action"]
  for export in exports:
    if export["name"] == test["action"]["field"]:
      globaladdr = export["value"][1]
      value = store["globals"][globaladdr]["value"]
      return [value]
      #num_tests_tried+=1
      #if value != test["expected"][0]["value"]:
      #  if verbose>1: print("SUCCESS")
        #num_tests_passed+=1
      #else:
      #  if verbose>1: print("FAILURE")



################################################
# Loop over each test in a <test>.json test file
################################################

def run_test_file(jsonfilename):
  d = None
  with open(jsonfilename) as f:
    d = json.load(f)
  if d==None: return -1
  #print(d)
  #print(json.dumps(d,indent=2))
  if "source_filename" not in d:
    print("this may not be a valid wabt test file")
    return -1
  if verbose>-1: print("\n\n\nrunning tests in "+d["source_filename"])
  tests = d["commands"]
  modules = { }		#all moduleinst's indexed by their names, used to call funcs and resolve exports
  registered_modules={}	#all moduleinst's which can be imported from, indexed by their registered name
  store = pywebassembly.init_store()	#done once and lasts for lifetime of this abstract machine
  instantiate_spectest_module(store,modules,registered_modules)	#module "spectest" is imported from by many tests
  registered_modules["spectest"] = modules["spectest"]	#register module "spectest" to be import-able
  moduleinst = None
  num_tests_passed = 0
  num_tests_tried = 0
  for idx,test in enumerate(tests):	#iterate over tests in this file
    if verbose>1: print("\ntest #",idx, test["type"])
    num_tests_tried += 1
    if test["type"] == "module":		#module
      store,moduleinst = test_opcode_module(test,store,modules,registered_modules)
      if moduleinst: num_tests_passed+=1
    elif test["type"] == "register":		#register
      test_opcode_register(test,store,modules,registered_modules,moduleinst)
      num_tests_passed+=1
    elif test["type"] == "action":		#action
      test_opcode_action(test,store,modules,registered_modules,moduleinst)
      num_tests_passed+=1
    elif test["type"][:7] == "assert_":		#assertion
      ret = test_opcode_assertion(test,store,modules,registered_modules,moduleinst)
      if test["type"] != "assert_return": num_tests_tried -= 1	#hack to only count assert_return for not
      if ret=="success": num_tests_passed+=1
  if verbose>-1: print("\nPassed",num_tests_passed,"out of",num_tests_tried,"tests   (actually ",len(tests),"total tests, some test opcodes not implemented yet)")






if __name__ == "__main__":
  import sys
  if "-h" in sys.argv or "--help" in sys.argv:
    if verbose>1: print("arguments should be list of json files filename.json")
    if verbose>1: print("or no arguments means run on every json in directory")
  #get .json filename(s)
  filenames = []
  if len(sys.argv)==1: #no args
    #get each json filename in dir
    import os
    for filename in os.listdir('.'):
      if filename[-5:] != ".json": continue
      filenames+=[filename]
  else:
    for arg in sys.argv[1:]:
      if arg[-5:]==".json":
        filenames+=[arg]
  #run test on each filename
  for file_ in filenames:
    res = run_test_file(file_)
    #if verbose>1: print(res)

