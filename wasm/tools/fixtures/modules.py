import logging
from typing import (
    Tuple,
)

import numpy

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
from wasm.execution import (
    Configuration,
)
from wasm.typing import (
    TValue,
)


def instantiate_spectest_module(store: Store) -> ModuleInstance:
    logger = logging.getLogger("wasm.tools.fixtures.modules.spectest")

    def spectest__print_i32(config: Configuration, args: Tuple[TValue, ...]) -> Tuple[TValue, ...]:
        logger.debug('print_i32: %s', args)
        return tuple()

    def spectest__print_i64(config: Configuration, args: Tuple[TValue, ...]) -> Tuple[TValue, ...]:
        logger.debug('print_i64: %s', args)
        return tuple()

    def spectest__print_f32(config: Configuration, args: Tuple[TValue, ...]) -> Tuple[TValue, ...]:
        logger.debug('print_f32: %s', args)
        return tuple()

    def spectest__print_f64(config: Configuration, args: Tuple[TValue, ...]) -> Tuple[TValue, ...]:
        logger.debug('print_f64: %s', args)
        return tuple()

    def spectest__print_i32_f32(config: Configuration,
                                args: Tuple[TValue, ...]) -> Tuple[TValue, ...]:
        logger.debug('print_i32_f32: %s', args)
        return tuple()

    def spectest__print_f64_f64(config: Configuration,
                                args: Tuple[TValue, ...]) -> Tuple[TValue, ...]:
        logger.debug('print_f64_f64: %s', args)
        return tuple()

    def spectest__print(config: Configuration, args: Tuple[TValue, ...]) -> Tuple[TValue, ...]:
        logger.debug('print: %s', args)
        return tuple()

    store.allocate_host_function(FunctionType((ValType.i32,), ()), spectest__print_i32)
    store.allocate_host_function(FunctionType((ValType.i64,), ()), spectest__print_i64)
    store.allocate_host_function(FunctionType((ValType.f32,), ()), spectest__print_f32)
    store.allocate_host_function(FunctionType((ValType.f64,), ()), spectest__print_f64)
    store.allocate_host_function(
        FunctionType((ValType.i32, ValType.f32), ()),
        spectest__print_i32_f32
    )
    store.allocate_host_function(
        FunctionType((ValType.f64, ValType.f64), ()),
        spectest__print_f64_f64
    )
    store.allocate_host_function(FunctionType((), ()), spectest__print)

    # min:1,max:2 required by import.wast:
    store.allocate_memory(MemoryType(numpy.uint32(1), numpy.uint32(2)))

    # 666 required by import.wast
    store.allocate_global(GlobalType(Mutability.const, ValType.i32), numpy.uint32(666))

    store.allocate_global(GlobalType(Mutability.const, ValType.f32), numpy.float32(0.0))
    store.allocate_global(GlobalType(Mutability.const, ValType.f64), numpy.float64(0.0))
    store.allocate_table(
        TableType(Limits(numpy.uint32(10), numpy.uint32(20)), FunctionAddress)
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
def instantiate_test_module(store: Store) -> ModuleInstance:
    def test__func(config: Configuration, args: Tuple[TValue, ...]) -> Tuple[TValue, ...]:
        return tuple()

    def test__func_i32(config: Configuration, args: Tuple[TValue, ...]) -> Tuple[TValue, ...]:
        return tuple()

    def test__func_f32(config: Configuration, args: Tuple[TValue, ...]) -> Tuple[TValue, ...]:
        return tuple()

    def test__func__i32(config: Configuration, args: Tuple[TValue, ...]) -> Tuple[TValue, ...]:
        return tuple()

    def test__func__f32(config: Configuration, args: Tuple[TValue, ...]) -> Tuple[TValue, ...]:
        return tuple()

    def test__func_i32_i32(config: Configuration, args: Tuple[TValue, ...]) -> Tuple[TValue, ...]:
        return tuple()

    def test__func_i64_i64(config: Configuration, args: Tuple[TValue, ...]) -> Tuple[TValue, ...]:
        return tuple()

    store.allocate_host_function(FunctionType((), ()), test__func)
    store.allocate_host_function(FunctionType((ValType.i32,), ()), test__func_i32)
    store.allocate_host_function(FunctionType((ValType.f32,), ()), test__func_f32)
    store.allocate_host_function(FunctionType((), (ValType.i32,)), test__func__i32)
    store.allocate_host_function(FunctionType((), (ValType.f32,)), test__func__f32)
    store.allocate_host_function(
        FunctionType((ValType.i32,), (ValType.i32,)),
        test__func_i32_i32,
    )
    store.allocate_host_function(
        FunctionType((ValType.i64,), (ValType.i64,)),
        test__func_i64_i64,
    )

    store.allocate_memory(MemoryType(numpy.uint32(1), None))
    store.allocate_global(GlobalType(Mutability.const, ValType.i32), numpy.uint32(666))
    store.allocate_global(GlobalType(Mutability.const, ValType.f32), numpy.float32(0.0))
    store.allocate_table(TableType(Limits(numpy.uint32(10), None), FunctionAddress))
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
