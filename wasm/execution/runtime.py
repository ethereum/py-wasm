from pathlib import (
    Path,
)
from typing import (
    IO,
    Dict,
    Iterable,
    Optional,
    Tuple,
    Union,
    cast,
)

import numpy

from wasm._utils.decorators import (
    to_tuple,
)
from wasm.datatypes import (
    DataSegment,
    ElementSegment,
    FunctionAddress,
    FunctionInstance,
    GlobalAddress,
    HostFunction,
    Import,
    MemoryAddress,
    Module,
    ModuleInstance,
    Store,
    TableAddress,
)
from wasm.exceptions import (
    InvalidModule,
    MalformedModule,
    ParseError,
    Unlinkable,
    ValidationError,
)
from wasm.parsers import (
    parse_module,
)
from wasm.typing import (
    TValue,
)
from wasm.validation import (
    validate_external_type_match,
    validate_module,
)

from .configuration import (
    Configuration,
)
from .instructions import (
    InstructionSequence,
)
from .stack import (
    Frame,
)

TAddress = Union[FunctionAddress, TableAddress, MemoryAddress, GlobalAddress]


@to_tuple
def _get_import_addresses(runtime: 'Runtime',
                          imports: Tuple[Import, ...]) -> Iterable[TAddress]:
    """
    Helper function to normalize the descriptors from a set of Imports to their
    addresses.
    """
    for import_ in imports:
        if not runtime.has_module(import_.module_name):
            raise Unlinkable(f"Runtime has no known module named '{import_.module_name}'")
        module = runtime.get_module(import_.module_name)
        for export in module.exports:
            if export.name == import_.as_name:
                yield export.value
                break
        else:
            raise Unlinkable(
                f"No export found with name '{import_.as_name}'"
            )


@to_tuple
def _initialize_globals(store: Store,
                        module: Module,
                        globals_addresses: Tuple[GlobalAddress, ...],
                        ) -> Iterable[TValue]:
    """
    Helper function for running the initialization code for the Globals
    to compute their initial values.
    """
    module_instances = ModuleInstance(
        types=(),
        func_addrs=(),
        memory_addrs=(),
        table_addrs=(),
        global_addrs=globals_addresses,
        exports=(),
    )

    for global_ in module.globals:
        config = Configuration(store=store)
        frame = Frame(
            module=module_instances,
            locals=[],
            instructions=InstructionSequence(global_.init),
            arity=1,
        )
        config.push_frame(frame)
        result = config.execute()
        if len(result) != 1:
            raise Exception("Invariant: globals initialization returned empty result")
        yield result[0]


@to_tuple
def _compute_table_offsets(store: Store,
                           elements: Tuple[ElementSegment, ...],
                           module_instance: ModuleInstance) -> Iterable[numpy.uint32]:
    """
    Helper function for running the initialization code for the ElementSegment
    objects to compute the table indices
    """
    for element_segment in elements:
        frame = Frame(
            module=module_instance,
            locals=[],
            instructions=InstructionSequence(element_segment.offset),
            arity=1,
        )
        config = Configuration(store=store)
        config.push_frame(frame)
        result = config.execute()
        if len(result) != 1:
            raise Exception("Invariant: element segment offset returned empty result")
        offset = numpy.uint32(cast(int, result[0]))

        table_address = module_instance.table_addrs[element_segment.table_idx]
        table_instance = store.tables[table_address]

        if offset + len(element_segment.init) > len(table_instance.elem):
            raise Unlinkable(
                f"Computed element segment offset exceeds table size: {offset} "
                f"+ {len(element_segment.init)} > {len(table_instance.elem)}"
            )
        yield offset


@to_tuple
def _compute_data_offsets(store: Store,
                          datas: Tuple[DataSegment, ...],
                          module_instance: ModuleInstance) -> Iterable[numpy.uint32]:
    """
    Helper function for running the initialization code for the DataSegment
    objects to compute the memory offsets.
    """
    for data_segment in datas:
        frame = Frame(
            module=module_instance,
            locals=[],
            instructions=InstructionSequence(data_segment.offset),
            arity=1,
        )
        config = Configuration(store=store)
        config.push_frame(frame)
        result = config.execute()
        if len(result) != 1:
            raise Exception("Invariant: data segment offset returned empty result")
        offset = numpy.uint32(cast(int, result[0]))

        memory_address = module_instance.memory_addrs[data_segment.memory_idx]
        memory_instance = store.mems[memory_address]

        if offset + len(data_segment.init) > len(memory_instance.data):
            raise Unlinkable(
                f"Computed data segment offset exceeds memory size: {offset} "
                f"+ {len(data_segment.init)} > {len(memory_instance.data)}"
            )
        yield offset


class Runtime:
    """
    Represents the *runtime* for the py-wasm WebAssembly interpreter.
    """
    store: Store
    modules: Dict[str, ModuleInstance]

    def __init__(self):
        self.store = Store()
        self.modules = {}

    def register_module(self, name: str, module: ModuleInstance) -> None:
        """
        Register a module under the provided name in this runtime.  This makes
        it available for other modules to import.
        """
        self.modules[name] = module

    def has_module(self, name: str) -> bool:
        """
        Return boolean whether a module is present in this runtime.
        """
        return name in self.modules

    def get_module(self, name: str) -> ModuleInstance:
        """
        Return the module instance registered for the provided name from this
        runtime.
        """
        return self.modules[name]

    def _get_import_addresses(self, imports: Tuple[Import, ...]) -> Tuple[TAddress, ...]:
        return _get_import_addresses(self, imports)

    def load_module(self, file_path: Path) -> Module:
        """
        Load a WebAssembly module from its binary source file.
        """
        if file_path.suffix != ".wasm":
            raise Exception("Unsupported file type: {file_path.suffix}")

        with file_path.open("rb") as wasm_file:
            try:
                module = parse_module(wasm_file)
            except ParseError as err:
                raise MalformedModule from err

        try:
            validate_module(module)
        except ValidationError as err:
            raise InvalidModule from err

        return module

    def load_buffer(self, buffer: IO) -> Module:
        """
        Load a WebAssembly module from its binary source file.
        """
        try:
            module = parse_module(buffer)
        except ParseError as err:
            raise MalformedModule from err

        try:
            validate_module(module)
        except ValidationError as err:
            raise InvalidModule from err

        return module

    def instantiate_module(self,
                           module: Module,
                           ) -> Tuple[ModuleInstance, Optional[Tuple[TValue, ...]]]:
        """
        Instantiate a WebAssembly module into this runtime environment.
        """
        # Ensure the module is valid
        try:
            module_import_types, module_export_types = validate_module(module)
        except ValidationError as err:
            raise InvalidModule from err

        # Gather all of the addresses for the external types for this module.
        all_import_addresses = self._get_import_addresses(module.imports)

        # Validate all of the addresses are known to the store.
        for address in all_import_addresses:
            try:
                self.store.validate_address(address)
            except ValidationError as err:
                raise InvalidModule from err

        # Gather the types for each of the values referenced by the addresses
        # of the module imports.
        store_import_types = tuple(
            self.store.get_type_for_address(address)
            for address in all_import_addresses
        )
        if len(module_import_types) != len(store_import_types):
            # TODO: This validation may be superfluous as both of these values
            # are generated from `module.imports` and the generation process
            # **should** give strong guarantees that the resulting list is the
            # same length as `module.imports`.
            raise Unlinkable(
                f"Mismatched number of import types: {len(module_import_types)} != "
                f"{len(store_import_types)}"
            )

        # Ensure that the module's internal types for it's imports match the
        # types found in the store.
        for module_type, store_type in zip(module_import_types, store_import_types):
            try:
                validate_external_type_match(store_type, module_type)
            except ValidationError as err:
                raise Unlinkable from err

        global_addresses = GlobalAddress.filter(all_import_addresses)
        global_values = _initialize_globals(self.store, module, global_addresses)

        module_instance = self.store.allocate_module(module, all_import_addresses, global_values)

        element_segment_offsets = _compute_table_offsets(
            self.store,
            module.elem,
            module_instance,
        )
        data_segment_offsets = _compute_data_offsets(
            self.store,
            module.data,
            module_instance,
        )

        for offset, element_segment in zip(element_segment_offsets, module.elem):
            for idx, function_idx in enumerate(element_segment.init):
                function_address = module_instance.func_addrs[function_idx]
                table_address = module_instance.table_addrs[element_segment.table_idx]
                table_instance = self.store.tables[table_address]
                table_instance.elem[offset + idx] = function_address

        for offset, data_segment in zip(data_segment_offsets, module.data):
            memory_address = module_instance.memory_addrs[data_segment.memory_idx]
            memory_instance = self.store.mems[memory_address]
            data_length = len(data_segment.init)
            memory_instance.data[offset:offset + data_length] = data_segment.init

        result: Optional[Tuple[TValue, ...]]

        if module.start is not None:
            function_address = module_instance.func_addrs[module.start.function_idx]
            result = self.invoke_function(function_address)
        else:
            result = None

        return module_instance, result

    def get_configuration(self) -> Configuration:
        return Configuration(self.store)

    def invoke_function(self,
                        function_address: FunctionAddress,
                        function_args: Tuple[TValue, ...] = None,) -> Tuple[TValue, ...]:
        """
        Invoke a function denoted by the function address with the provided arguments.
        """
        try:
            function = self.store.funcs[function_address]
        except IndexError:
            raise TypeError(
                f"Function address out of range: {function_address} >= "
                f"{len(self.store.funcs)}"
            )
        if function_args is None:
            function_args = tuple()

        for arg, valtype in zip(function_args, function.type.params):
            valtype.validate_arg(arg)

        config = self.get_configuration()

        if isinstance(function, FunctionInstance):
            from wasm.logic.control import _setup_function_invocation
            _setup_function_invocation(config, function_address, function_args)
            ret = config.execute()
            return ret
        elif isinstance(function, HostFunction):
            ret = function.hostcode(config, function_args)
            return ret
        else:
            raise Exception(f"Invariant: unknown function type: {type(function)}")
