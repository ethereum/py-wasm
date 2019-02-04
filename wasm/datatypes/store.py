from typing import (
    List,
    Union,
)

from wasm import (
    constants,
)
from wasm.typing import (
    HostFunctionCallable,
    TValue,
)

from .addresses import (
    FunctionAddress,
    GlobalAddress,
    MemoryAddress,
    TableAddress,
)
from .function import (
    Function,
    FunctionType,
    HostFunction,
)
from .globals import (
    GlobalInstance,
    GlobalType,
)
from .memory import (
    MemoryInstance,
    MemoryType,
)
from .module import (
    FunctionInstance,
    ModuleInstance,
)
from .table import (
    TableInstance,
    TableType,
)


class Store:
    funcs: List[Union[FunctionInstance, HostFunction]]
    mems: List[MemoryInstance]
    tables: List[TableInstance]
    globals: List[GlobalInstance]

    def __init__(self) -> None:
        self.funcs = []
        self.mems = []
        self.tables = []
        self.globals = []

    def allocate_function(self, module: ModuleInstance, function: Function) -> FunctionAddress:
        function_address = FunctionAddress(len(self.funcs))
        function_type = module.types[function.type_idx]
        function_instance = FunctionInstance(function_type, module, function)
        self.funcs.append(function_instance)
        return function_address

    def allocate_host_function(self,
                               function_type: FunctionType,
                               hostfunc: HostFunctionCallable) -> FunctionAddress:
        function_address = FunctionAddress(len(self.funcs))
        function_instance = HostFunction(function_type, hostfunc)
        self.funcs.append(function_instance)
        return function_address

    def allocate_table(self, table_type: TableType) -> TableAddress:
        table_address = TableAddress(len(self.tables))
        table_instance = TableInstance(
            elem=[None] * table_type.limits.min,
            max=table_type.limits.max,
        )
        self.tables.append(table_instance)
        return table_address

    def allocate_memory(self, memory_type: MemoryType) -> MemoryAddress:
        memory_address = MemoryAddress(len(self.mems))
        memory_instance = MemoryInstance(
            data=bytearray(memory_type.min * constants.PAGE_SIZE_64K),
            max=memory_type.max,
        )
        self.mems.append(memory_instance)
        return memory_address

    def allocate_global(self, global_type: GlobalType, value: TValue) -> GlobalAddress:
        global_address = GlobalAddress(len(self.globals))
        global_instance = GlobalInstance(global_type.valtype, value, global_type.mut)
        self.globals.append(global_instance)
        return global_address
