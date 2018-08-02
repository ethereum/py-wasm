
import sys
sys.path.append('..')
import pywebassembly as wasm

#set up VM for multiple modules
store = wasm.init_store()                               #do this once for each VM instance
modules = { }         #all moduleinst's indexed by their names, used to call funcs and resolve exports

#instantiate first module
file_ = open('mod1.wasm', 'rb')
bytestar = memoryview(file_.read())                     #can also use bytearray or bytes instead of memoryview
module = wasm.decode_module(bytestar)                   #get module as abstract syntax
externvalstar = []                                      #imports, none for fibonacci.wasm
store,moduleinst,ret = wasm.instantiate_module(store,module,externvalstar)

#register this module instance so it can be imported from
modules["mod1"] = moduleinst

#instantiate second module
file_ = open('mod2.wasm', 'rb')
bytestar = memoryview(file_.read())                     #can also use bytearray or bytes instead of memoryview
module = wasm.decode_module(bytestar)                   #get module as abstract syntax
externvalstar = []                                      #imports, none for fibonacci.wasm
for import_ in module["imports"]:			#for each import, look for it's matching export
  importmoduleinst = modules[import_["module"]]
  externval = None
  for export in importmoduleinst["exports"]:
    if export["name"] == import_["name"]:
      externval = export["value"]
  if externval[0] != import_["desc"][0]: print("unlinkable")  #error: import type (func, table, mem, globa) doesn't match
  externvalstar += [externval]
store,moduleinst,ret = wasm.instantiate_module(store,module,externvalstar)
modules["mod2"] = moduleinst

#call function
externval = wasm.get_export(modules["mod2"], "f1")          #we want to call the function "fib"
funcaddr = externval[1]                                 #the address of the funcinst for "fib"
store,ret = wasm.invoke_func(store,funcaddr,[])       #finally, invoke the function

print(ret)                                              #list of return values, limitted to one value in Wasm 1.0

