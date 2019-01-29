import logging

import wasm
from wasm.datatypes import (
    Export,
    FuncIdx,
    FuncRef,
    FunctionType,
    GlobalIdx,
    GlobalType,
    Limits,
    MemoryIdx,
    MemoryType,
    Mutability,
    TableIdx,
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

    wasm.alloc_func(store, FunctionType((ValType.i32,), ()), spectest__print_i32)
    wasm.alloc_func(store, FunctionType((ValType.i64,), ()), spectest__print_i64)
    wasm.alloc_func(store, FunctionType((ValType.f32,), ()), spectest__print_f32)
    wasm.alloc_func(store, FunctionType((ValType.f64,), ()), spectest__print_f64)
    wasm.alloc_func(store, FunctionType((ValType.i32, ValType.f32), ()), spectest__print_i32_f32)
    wasm.alloc_func(store, FunctionType((ValType.f64, ValType.f64), ()), spectest__print_f64_f64)
    wasm.alloc_func(store, FunctionType((), ()), spectest__print)

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
            FunctionType((ValType.i32,), ()),
            FunctionType((ValType.i64,), ()),
            FunctionType((ValType.f32,), ()),
            FunctionType((ValType.f64,), ()),
            FunctionType((ValType.i32, ValType.f32), ()),
            FunctionType((ValType.f64, ValType.f64), ()),
            FunctionType((), ()),
        ],
        "funcaddrs": [FuncIdx(idx) for idx in range(7)],
        "tableaddrs": [TableIdx(0)],
        "memaddrs": [MemoryIdx(0)],
        "globaladdrs": [GlobalIdx(0), GlobalIdx(1)],
        "exports": [
            Export("print_i32", FuncIdx(0)),
            Export("print_i64", FuncIdx(1)),
            Export("print_f32", FuncIdx(2)),
            Export("print_f64", FuncIdx(3)),
            Export("print_i32_f32", FuncIdx(4)),
            Export("print_f64_f64", FuncIdx(5)),
            Export("print", FuncIdx(6)),
            Export("memory", MemoryIdx(0)),
            Export("global_i32", GlobalIdx(0)),
            Export("global_f32", GlobalIdx(1)),
            Export("global_f64", GlobalIdx(2)),
            Export("table", TableIdx(0)),
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

    wasm.alloc_func(store, FunctionType((), ()), test__func)
    wasm.alloc_func(store, FunctionType((ValType.i32,), ()), test__func_i32)
    wasm.alloc_func(store, FunctionType((ValType.f32,), ()), test__func_f32)
    wasm.alloc_func(store, FunctionType((), (ValType.i32,)), test__func__i32)
    wasm.alloc_func(store, FunctionType((), (ValType.f32,)), test__func__f32)
    wasm.alloc_func(store, FunctionType((ValType.i32,), (ValType.i32,)), test__func_i32_i32)
    wasm.alloc_func(store, FunctionType((ValType.i64,), (ValType.i64,)), test__func_i64_i64)
    wasm.alloc_mem(store, MemoryType(1, None))
    wasm.alloc_global(store, GlobalType(Mutability.const, ValType.i32), 666)
    wasm.alloc_global(store, GlobalType(Mutability.const, ValType.f32), 0.0)
    wasm.alloc_table(store, TableType(Limits(10, None), FuncRef))
    moduleinst = {
        "types": [
            FunctionType((), ()),
            FunctionType((ValType.i32,), ()),
            FunctionType((ValType.f32,), ()),
            FunctionType((), (ValType.i32,)),
            FunctionType((), (ValType.f32,)),
            FunctionType((ValType.i32,), (ValType.i32,)),
            FunctionType((ValType.i64,), (ValType.i64,)),
        ],
        "funcaddrs": [FuncIdx(idx) for idx in range(7)],
        "tableaddrs": [TableIdx(0)],
        "memaddrs": [MemoryIdx(0)],
        "globaladdrs": [GlobalIdx(0), GlobalIdx(1)],
        "exports": [
            Export("func", FuncIdx(0)),
            Export("func_i32", FuncIdx(1)),
            Export("func_f32", FuncIdx(2)),
            Export("func__i32", FuncIdx(3)),
            Export("func__f32", FuncIdx(4)),
            Export("func__i32_i32", FuncIdx(5)),
            Export("func__i64_i64", FuncIdx(6)),
            Export("memory-2-inf", MemoryIdx(0)),
            Export("global-i32", GlobalIdx(0)),
            Export("global-f32", GlobalIdx(1)),
            Export("table-10-inf", TableIdx(0)),
        ],
    }
    return moduleinst
