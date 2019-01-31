import logging

import wasm
from wasm.datatypes import (
    ExportInstance,
    FunctionAddress,
    FunctionType,
    GlobalAddress,
    GlobalType,
    Limits,
    MemoryAddress,
    MemoryType,
    ModuleInstance,
    Mutability,
    Store,
    TableAddress,
    TableType,
    ValType,
)
from wasm.typing import (
    UInt32,
)


def instantiate_spectest_module(store: Store) -> ModuleInstance:
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
    wasm.alloc_mem(store, MemoryType(UInt32(1), UInt32(2)))

    # 666 required by import.wast
    wasm.alloc_global(store, GlobalType(Mutability.const, ValType.i32), 666)

    wasm.alloc_global(store, GlobalType(Mutability.const, ValType.f32), 0.0)
    wasm.alloc_global(store, GlobalType(Mutability.const, ValType.f64), 0.0)
    wasm.alloc_table(
        store, TableType(Limits(UInt32(10), UInt32(20)), FunctionAddress)
    )  # max was 30, changed to 20 for import.wast
    moduleinst = ModuleInstance(
        types=(
            FunctionType((ValType.i32,), ()),
            FunctionType((ValType.i64,), ()),
            FunctionType((ValType.f32,), ()),
            FunctionType((ValType.f64,), ()),
            FunctionType((ValType.i32, ValType.f32), ()),
            FunctionType((ValType.f64, ValType.f64), ()),
            FunctionType((), ()),
        ),
        func_addrs=tuple(FunctionAddress(idx) for idx in range(7)),
        table_addrs=(TableAddress(0),),
        memory_addrs=(MemoryAddress(0),),
        global_addrs=(GlobalAddress(0), GlobalAddress(1)),
        exports=(
            ExportInstance("print_i32", FunctionAddress(0)),
            ExportInstance("print_i64", FunctionAddress(1)),
            ExportInstance("print_f32", FunctionAddress(2)),
            ExportInstance("print_f64", FunctionAddress(3)),
            ExportInstance("print_i32_f32", FunctionAddress(4)),
            ExportInstance("print_f64_f64", FunctionAddress(5)),
            ExportInstance("print", FunctionAddress(6)),
            ExportInstance("memory", MemoryAddress(0)),
            ExportInstance("global_i32", GlobalAddress(0)),
            ExportInstance("global_f32", GlobalAddress(1)),
            ExportInstance("global_f64", GlobalAddress(2)),
            ExportInstance("table", TableAddress(0)),
        ),
    )
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
    wasm.alloc_table(store, TableType(Limits(10, None), FunctionAddress))
    moduleinst = ModuleInstance(
        types=(
            FunctionType((), ()),
            FunctionType((ValType.i32,), ()),
            FunctionType((ValType.f32,), ()),
            FunctionType((), (ValType.i32,)),
            FunctionType((), (ValType.f32,)),
            FunctionType((ValType.i32,), (ValType.i32,)),
            FunctionType((ValType.i64,), (ValType.i64,)),
        ),
        func_addrs=tuple(FunctionAddress(idx) for idx in range(7)),
        table_addrs=(TableAddress(0),),
        memory_addrs=(MemoryAddress(0),),
        global_addrs=(GlobalAddress(0), GlobalAddress(1)),
        exports=(
            ExportInstance("func", FunctionAddress(0)),
            ExportInstance("func_i32", FunctionAddress(1)),
            ExportInstance("func_f32", FunctionAddress(2)),
            ExportInstance("func__i32", FunctionAddress(3)),
            ExportInstance("func__f32", FunctionAddress(4)),
            ExportInstance("func__i32_i32", FunctionAddress(5)),
            ExportInstance("func__i64_i64", FunctionAddress(6)),
            ExportInstance("memory-2-inf", MemoryAddress(0)),
            ExportInstance("global-i32", GlobalAddress(0)),
            ExportInstance("global-f32", GlobalAddress(1)),
            ExportInstance("table-10-inf", TableAddress(0)),
        ),
    )
    return moduleinst
