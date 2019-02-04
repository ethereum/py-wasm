from typing import (
    Iterable,
    List,
    Tuple,
    Union,
)

from wasm import (
    constants,
)
from wasm.exceptions import (
    ValidationError,
)
from wasm.typing import (
    HostFunctionCallable,
    TValue,
    UInt32,
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
from .limits import (
    Limits,
)
from .memory import (
    MemoryInstance,
    MemoryType,
)
from .module import (
    Export,
    ExportInstance,
    FunctionInstance,
    Module,
    ModuleInstance,
)
from .table import (
    TableInstance,
    TableType,
)

TAddress = Union[FunctionAddress, GlobalAddress, MemoryAddress, TableAddress]
TExtern = Union[FunctionType, TableType, MemoryType, GlobalType]


def _collate_exports(exports: Tuple[Export, ...],
                     function_addresses: Tuple[FunctionAddress, ...],
                     table_addresses: Tuple[TableAddress, ...],
                     memory_addresses: Tuple[MemoryAddress, ...],
                     global_addresses: Tuple[GlobalAddress, ...],
                     ) -> Iterable[ExportInstance]:
        for export in exports:
            if export.is_function:
                yield ExportInstance(export.name, function_addresses[export.function_idx])
            elif export.is_table:
                yield ExportInstance(export.name, table_addresses[export.table_idx])
            elif export.is_memory:
                yield ExportInstance(export.name, memory_addresses[export.memory_idx])
            elif export.is_global:
                yield ExportInstance(export.name, global_addresses[export.global_idx])
            else:
                raise Exception(
                    f"Invariant: unknown export descriptor type: {type(export.desc)}"
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

    def get_type_for_address(self, address: TAddress) -> TExtern:
        if isinstance(address, FunctionAddress):
            funcinst = self.funcs[address]
            return funcinst.type
        elif isinstance(address, TableAddress):
            tableinst = self.tables[address]
            return TableType(
                limits=Limits(UInt32(len(tableinst.elem)), tableinst.max),
                elem_type=FunctionAddress,
            )
        elif isinstance(address, MemoryAddress):
            meminst = self.mems[address]
            return MemoryType(
                UInt32(len(meminst.data) // constants.PAGE_SIZE_64K),
                meminst.max,
            )
        elif isinstance(address, GlobalAddress):
            globalinst = self.globals[address]
            return GlobalType(
                globalinst.mut,
                globalinst.valtype,
            )
        else:
            raise Exception(f"Invariant: unknown address type: {type(address)}")

    def validate_address(self, address: TAddress) -> None:
        if isinstance(address, FunctionAddress):
            self.validate_function_address(address)
        elif isinstance(address, TableAddress):
            self.validate_table_address(address)
        elif isinstance(address, MemoryAddress):
            self.validate_memory_address(address)
        elif isinstance(address, GlobalAddress):
            self.validate_global_address(address)
        else:
            raise Exception(f"Invariant: unknown address type: {type(address)}")

    #
    # Functions
    #
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

    def validate_function_address(self, address: FunctionAddress) -> None:
        if address >= len(self.funcs):
            raise ValidationError(
                f"Function address outside of valid range: {address} >= {len(self.funcs)}"
            )

    #
    # Tables
    #
    def allocate_table(self, table_type: TableType) -> TableAddress:
        table_address = TableAddress(len(self.tables))
        table_instance = TableInstance(
            elem=[None] * table_type.limits.min,
            max=table_type.limits.max,
        )
        self.tables.append(table_instance)
        return table_address

    def validate_table_address(self, address: TableAddress) -> None:
        if address >= len(self.tables):
            raise ValidationError(
                f"Table address outside of valid range: {address} >= {len(self.tables)}"
            )

    #
    # Memory
    #
    def allocate_memory(self, memory_type: MemoryType) -> MemoryAddress:
        memory_address = MemoryAddress(len(self.mems))
        memory_instance = MemoryInstance(
            data=bytearray(memory_type.min * constants.PAGE_SIZE_64K),
            max=memory_type.max,
        )
        self.mems.append(memory_instance)
        return memory_address

    def validate_memory_address(self, address: MemoryAddress) -> None:
        if address >= len(self.mems):
            raise ValidationError(
                f"Memory address outside of valid range: {address} >= {len(self.mems)}"
            )

    #
    # Globals
    #
    def allocate_global(self, global_type: GlobalType, value: TValue) -> GlobalAddress:
        global_address = GlobalAddress(len(self.globals))
        global_instance = GlobalInstance(global_type.valtype, value, global_type.mut)
        self.globals.append(global_instance)
        return global_address

    def validate_global_address(self, address: GlobalAddress) -> None:
        if address >= len(self.globals):
            raise ValidationError(
                f"Global address outside of valid range: {address} >= {len(self.globals)}"
            )

    #
    # Modules
    #
    def allocate_module(self,
                        module: Module,
                        all_import_addresses: Tuple[TAddress, ...],
                        globals_values: Tuple[TValue, ...],
                        ) -> ModuleInstance:
        if len(globals_values) != len(module.globals):
            raise Exception(
                f"Length mismatch for declared module globals and provided "
                f"globals values: {len(module.globals)} != {len(globals_values)}"
            )

        next_function_address = len(self.funcs)

        module_function_addresses = tuple(
            FunctionAddress(addr)
            for addr
            in range(next_function_address, next_function_address + len(module.funcs))
        )
        module_table_addresses = tuple(self.allocate_table(table.type) for table in module.tables)
        module_memory_addresses = tuple(self.allocate_memory(mem.type) for mem in module.mems)
        module_globals_addresses = tuple(
            self.allocate_global(global_.type, value)
            for global_, value in zip(module.globals, globals_values)
        )

        function_addresses = (
            FunctionAddress.filter(all_import_addresses) + module_function_addresses
        )
        table_addresses = TableAddress.filter(all_import_addresses) + module_table_addresses
        memory_addresses = MemoryAddress.filter(all_import_addresses) + module_memory_addresses
        global_addresses = GlobalAddress.filter(all_import_addresses) + module_globals_addresses

        exports = tuple(_collate_exports(
            exports=module.exports,
            function_addresses=function_addresses,
            table_addresses=table_addresses,
            memory_addresses=memory_addresses,
            global_addresses=global_addresses,
        ))

        module_instance = ModuleInstance(
            types=module.types,
            func_addrs=function_addresses,
            table_addrs=table_addresses,
            memory_addrs=memory_addresses,
            global_addrs=global_addresses,
            exports=exports,
        )

        # We have to perform the actual function allocations *after* module
        # instantiation because there is a circular dependency between the
        # Store/FunctionInstance/ModuleInstance.  This is solved by
        # pre-computing the function addresses that will be allocated prior to
        # instantiating the module instance, and then performing the
        # allocation.
        store_function_addresses = tuple(
            self.allocate_function(module_instance, function)
            for function in module.funcs
        )
        if store_function_addresses != module_function_addresses:
            raise Exception(
                "Invariant: actual function addresses don't match expected values:\n"
                f" - store : {store_function_addresses}\n"
                f" - actual: {module_function_addresses}"
            )

        return module_instance
