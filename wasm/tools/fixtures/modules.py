import logging

import wasm
from wasm.datatypes import (
    FuncRef,
    FuncType,
    GlobalType,
    Limits,
    MemoryType,
    Mutability,
    TableType,
    ValType,
)


def instantiate_spectest_module(store):
    logger = logging.getLogger("wasm.tools.fixtures.modules.spectest")

    def spectest__print_i32(store, arg):
        logger.debug('print_i32: %s', arg)
        return store, []

    def spectest__print_i64(store, arg):
        logger.debug('print_i64: %s', arg)
        return store, []

    def spectest__print_f32(store, arg):
        logger.debug('print_f32: %s', arg)
        return store, []

    def spectest__print_f64(store, arg):
        logger.debug('print_f64: %s', arg)
        return store, []

    def spectest__print_i32_f32(store, arg):
        logger.debug('print_i32_f32: %s', arg)
        return store, []

    def spectest__print_f64_f64(store, arg):
        logger.debug('print_f64_f64: %s', arg)
        return store, []

    def spectest__print(store, arg):
        logger.debug('print: %s', arg)
        return store, []

    wasm.alloc_func(store, FuncType((ValType.i32,), ()), spectest__print_i32)
    wasm.alloc_func(store, FuncType((ValType.i64,), ()), spectest__print_i64)
    wasm.alloc_func(store, FuncType((ValType.f32,), ()), spectest__print_f32)
    wasm.alloc_func(store, FuncType((ValType.f64,), ()), spectest__print_f64)
    wasm.alloc_func(store, FuncType((ValType.i32, ValType.f32), ()), spectest__print_i32_f32)
    wasm.alloc_func(store, FuncType((ValType.f64, ValType.f64), ()), spectest__print_f64_f64)
    wasm.alloc_func(store, FuncType((), ()), spectest__print)

    # min:1,max:2 required by import.wast:
    wasm.alloc_mem(store, MemoryType(1, 2))

    # 666 required by import.wast
    wasm.alloc_global(store, GlobalType(Mutability.const, ValType.i32), 666)

    wasm.alloc_global(store, GlobalType(Mutability.const, ValType.f32), 0.0)
    wasm.alloc_global(store, GlobalType(Mutability.const, ValType.f64), 0.0)
    wasm.alloc_table(
        store, TableType(Limits(10, 20), FuncRef)
    )  # max was 30, changed to 20 for import.wast
    moduleinst = {
        "types": [
            FuncType((ValType.i32,), ()),
            FuncType((ValType.i64,), ()),
            FuncType((ValType.f32,), ()),
            FuncType((ValType.f64,), ()),
            FuncType((ValType.i32, ValType.f32), ()),
            FuncType((ValType.f64, ValType.f64), ()),
            FuncType((), ()),
        ],
        "funcaddrs": [0, 1, 2, 3, 4, 5, 6],
        "tableaddrs": [0],
        "memaddrs": [0],
        "globaladdrs": [0, 1, 2],
        "exports": [
            {"name": "print_i32", "value": ["func", 0]},
            {"name": "print_i64", "value": ["func", 1]},
            {"name": "print_f32", "value": ["func", 2]},
            {"name": "print_f64", "value": ["func", 3]},
            {"name": "print_i32_f32", "value": ["func", 4]},
            {"name": "print_f64_f64", "value": ["func", 5]},
            {"name": "print", "value": ["func", 6]},
            {"name": "memory", "value": ["mem", 0]},
            {"name": "global_i32", "value": ["global", 0]},
            {"name": "global_f32", "value": ["global", 1]},
            {"name": "global_f64", "value": ["global", 2]},
            {"name": "table", "value": ["table", 0]},
        ],
    }
    return moduleinst


# this module called "wast" is used by import.wast to test for assert_unlinkable
def instantiate_test_module(store):
    def test__func(store, arg):
        pass

    def test__func_i32(store, arg):
        pass

    def test__func_f32(store, arg):
        pass

    def test__func__i32(store, arg):
        pass

    def test__func__f32(store, arg):
        pass

    def test__func_i32_i32(store, arg):
        pass

    def test__func_i64_i64(store, arg):
        pass

    wasm.alloc_func(store, FuncType((), ()), test__func)
    wasm.alloc_func(store, FuncType((ValType.i32,), ()), test__func_i32)
    wasm.alloc_func(store, FuncType((ValType.f32,), ()), test__func_f32)
    wasm.alloc_func(store, FuncType((), (ValType.i32,)), test__func__i32)
    wasm.alloc_func(store, FuncType((), (ValType.f32,)), test__func__f32)
    wasm.alloc_func(store, FuncType((ValType.i32,), (ValType.i32,)), test__func_i32_i32)
    wasm.alloc_func(store, FuncType((ValType.i64,), (ValType.i64,)), test__func_i64_i64)
    wasm.alloc_mem(store, MemoryType(1, None))
    wasm.alloc_global(store, GlobalType(Mutability.const, ValType.i32), 666)
    wasm.alloc_global(store, GlobalType(Mutability.const, ValType.f32), 0.0)
    wasm.alloc_table(store, TableType(Limits(10, None), FuncRef))
    moduleinst = {
        "types": [
            FuncType((), ()),
            FuncType((ValType.i32,), ()),
            FuncType((ValType.f32,), ()),
            FuncType((), (ValType.i32,)),
            FuncType((), (ValType.f32,)),
            FuncType((ValType.i32,), (ValType.i32,)),
            FuncType((ValType.i64,), (ValType.i64,)),
        ],
        "funcaddrs": [0, 1, 2, 3, 4, 5, 6],
        "tableaddrs": [0],
        "memaddrs": [0],
        "globaladdrs": [0, 1],
        "exports": [
            {"name": "func", "value": ["func", 0]},
            {"name": "func_i32", "value": ["func", 1]},
            {"name": "func_f32", "value": ["func", 2]},
            {"name": "func__i32", "value": ["func", 3]},
            {"name": "func__f32", "value": ["func", 4]},
            {"name": "func__i32_i32", "value": ["func", 5]},
            {"name": "func__i64_i64", "value": ["func", 6]},
            {"name": "memory-2-inf", "value": ["mem", 0]},
            {"name": "global-i32", "value": ["global", 0]},
            {"name": "global-f32", "value": ["global", 1]},
            {"name": "table-10-inf", "value": ["table", 0]},
        ],
    }
    return moduleinst
