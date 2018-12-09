#!/usr/bin/env python

"""
University of Illinois/NCSA Open Source License
Copyright (c) 2018 Paul Dworzanski
All rights reserved.

Developed by:           Paul Dworzanski
                        Ethereum Foundation
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal with the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimers.
Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimers in the documentation and/or other materials provided with the distribution.
Neither the names of Paul Dworzanski, Ethereum Foundation, nor the names of its contributors may be used to endorse or promote products derived from this Software without specific prior written permission.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS WITH THE SOFTWARE.
"""


import sys
sys.path.append('..')

from pywebassembly import *

def export_only_main_and_memory(mod):
  print("\nexports (should be main function and the memory):")
  for export_ in mod["exports"][:]:
    if export_["name"]=="_main":
      export_["name"]="main"
    if export_["name"] not in {"main","memory"}:
      mod["exports"].remove(export_)
  for export_ in mod["exports"][:]:
    print(export_)

def import_only_ethereum_eei(mod):
  print("\nimports (should be only ewasm helper functions):")
  for import_ in mod["imports"]:
    if import_["module"] != "ethereum":
      import_["module"] = "ethereum"
  for import_ in mod["imports"]:
    print(import_)

def parse_wasm_and_clean_up(filename):
  #print("reading ",filename)
  with open(filename, 'rb') as f:
    wasm = memoryview(f.read())
    mod = decode_module(wasm)
    export_only_main_and_memory(mod)
    import_only_ethereum_eei(mod)
    spec_binary_module_inv_to_file(mod,filename.rsplit('.',1)[0]+"_chiseled.wasm")


if __name__ == "__main__":
  import sys
  if len(sys.argv)!=2:
    print("Argument should be <filename>.wasm")
  else:
    parse_wasm_and_clean_up(sys.argv[1])

