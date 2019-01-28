from typing import (
    Optional,
    Tuple,
)

from wasm.datatypes import (
    FuncType,
    GlobalType,
    MemoryType,
    TableType,
    ValType,
)
from wasm.exceptions import (
    InvalidModule,
)


class Context:
    def __init__(self,
                 *,
                 types: Tuple[FuncType, ...],
                 funcs: Tuple[FuncType, ...],
                 tables: Tuple[TableType, ...],
                 mems: Tuple[MemoryType, ...],
                 globals: Tuple[GlobalType, ...],
                 locals: Tuple[ValType, ...],
                 labels: Tuple[ValType, ...],
                 returns: Optional[Tuple[ValType, ...]],
                 ) -> None:
        self.types = types
        self.funcs = funcs
        self.tables = tables
        self.mems = mems
        self.globals = globals
        self.locals = locals
        self.labels = labels
        self.returns = returns

    def prime(self,
              *,
              types: Tuple[FuncType, ...] = None,
              funcs: Tuple[FuncType, ...] = None,
              tables: Tuple[TableType, ...] = None,
              mems: Tuple[MemoryType, ...] = None,
              globals: Tuple[GlobalType, ...] = None,
              locals: Tuple[ValType, ...] = None,
              labels: Tuple[ValType, ...] = None,
              returns: Optional[Tuple[ValType, ...]] = None) -> 'Context':
        return type(self)(
            types=types or self.types,
            funcs=funcs or self.funcs,
            tables=tables or self.tables,
            mems=mems or self.mems,
            globals=globals or self.globals,
            locals=locals or self.locals,
            labels=labels or self.labels,
            returns=returns or self.returns,
        )

    #
    # Types
    #
    def validate_type_idx(self, idx: int) -> None:
        if not self.has_type(idx):
            raise InvalidModule(
                f"Types index outside of valid range: {idx} >= {len(self.types)}"
            )

    def has_type(self, idx: int) -> bool:
        return idx < len(self.types)

    def get_type(self, idx: int) -> FuncType:
        return self.types[idx]

    #
    # Functions
    #
    def validate_func_idx(self, idx: int) -> None:
        if not self.has_func(idx):
            raise InvalidModule(
                f"Function index outside of valid range: {idx} >= {len(self.funcs)}"
            )

    def has_func(self, idx: int) -> bool:
        return idx < len(self.funcs)

    def get_func(self, idx: int) -> FuncType:
        return self.funcs[idx]

    #
    # Tables
    #
    def validate_table_idx(self, idx: int) -> None:
        if not self.has_table(idx):
            raise InvalidModule(
                f"Table index outside of valid range: {idx} >= {len(self.tables)}"
            )

    def has_table(self, idx: int) -> bool:
        return idx < len(self.tables)

    def get_table(self, idx: int) -> TableType:
        return self.tables[idx]

    #
    # Memory
    #
    def validate_mem_idx(self, idx: int) -> None:
        if not self.has_mem(idx):
            raise InvalidModule(
                f"Memory index outside of valid range: {idx} >= {len(self.mems)}"
            )

    def has_mem(self, idx: int) -> bool:
        return idx < len(self.mems)

    def get_mem(self, idx: int) -> MemoryType:
        return self.mems[idx]

    #
    # Global
    #
    def validate_global_idx(self, idx: int) -> None:
        if not self.has_global(idx):
            raise InvalidModule(
                f"Global index outside of valid range: {idx} >= {len(self.globals)}"
            )

    def has_global(self, idx: int) -> bool:
        return idx < len(self.globals)

    def get_global(self, idx: int) -> GlobalType:
        return self.globals[idx]

    #
    # Locals
    #
    def validate_local_idx(self, idx: int) -> None:
        if not self.has_local(idx):
            raise InvalidModule(
                f"Locals index outside of valid range: {idx} >= {len(self.locals)}"
            )

    def has_local(self, idx: int) -> bool:
        return idx < len(self.locals)

    def get_local(self, idx: int) -> ValType:
        return self.locals[idx]
