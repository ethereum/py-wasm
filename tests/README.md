
# spec_tests.py

 This file runs official Wasm spec tests, including their extra opcodes for testing such as `assert_return` and `assert_trap`. Because PyWebAssembly does _not_ yet support text format `.wast` (or `.wat`) files, we use `wabt`'s `wast2json` to convert each `<test>.wast` to `<test>.wast.json` and corresponding `<test>.0.wasm`, `<test>.1.wasm`, ... . 

This python script parses the `<test>.wast.json` files and executes the tests. Currently, all tests pass except tests pass related to floating point `NaN`'s significand.  Execute this file as follows.

```
#execute this file on any <test>.wast.json test file
python3 spec_tests.py spec_tests/address.wast.json
#or execute this file on all .json test files
python3 spec_tests.py spec_tests/
```

Todo:
All spec tests are passing except some floating point tests involving the significand of `NaN`. I don't know how to do with the Python float type, so I hope that using ctypes `c_float` and `c_double` may be necessary.

# spec_tests/

This directory contains all spec tests, before and after they are transformed by wabt's `wast2json`. To update this directory:

```
#get latest PyWebAssembly
git clone https://github.com/poemm/pywebassembly.git

#compile wabt's tool wast2json
git clone https://github.com/WebAssembly/wabt.git
cd wabt
mkdir BUILD && cd BUILD
cmake .. -DBUILD_TESTS=OFF  #off if gtest not installed
make
cd ../..

#get official tests
git clone https://github.com/WebAssembly/spec.git

#convert official tests to json and wasm files
cd pywebassembly/tests/spec_tests
rm *
cp ../../../spec/test/core/*.wast .
#for each <test>.wast, execute: wast2json <test>.wast -o <test>.json
for filename in $(find *.wast 2> /dev/null); do
  ../../../wabt/BUILD/wast2json $filename -o $filename.json
done
cd ..
```
