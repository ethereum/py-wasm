from typing import (
    Optional,
    Tuple,
    Union,
)

from wasm.datatypes import (
    FuncIdx,
    FunctionType,
    GlobalIdx,
    GlobalType,
    LocalIdx,
    MemoryIdx,
    MemoryType,
    TableIdx,
    TableType,
    TypeIdx,
    ValType,
)
from wasm.exceptions import (
    ValidationError,
)

from .operand import (
    Operand,
)
from .stack import (
    ControlFrame,
    ControlStack,
    OperandStack,
)
from .unknown import (
    Unknown as _Unkown,
)

Unknown = _Unkown.Unknown


class BaseContext:
    types: Tuple[FunctionType, ...]
    functions: Tuple[FunctionType, ...]
    tables: Tuple[TableType, ...]
    mems: Tuple[MemoryType, ...]
    globals: Tuple[GlobalType, ...]
    locals: Tuple[ValType, ...]
    labels: Tuple[ValType, ...]
    # `returns` may be `None`, but the argument must be
    # explicitely supplied.
    returns: Union[None, Tuple[ValType, ...]]

    #
    # Types
    #
    def validate_type_idx(self, idx: TypeIdx) -> None:
        if not self.has_type(idx):
            raise ValidationError(
                f"Types index outside of valid range: {idx} >= {len(self.types)}"
            )

    def has_type(self, idx: TypeIdx) -> bool:
        return idx < len(self.types)

    def get_type(self, idx: TypeIdx) -> FunctionType:
        return self.types[idx]

    #
    # Functions
    #
    def validate_function_idx(self, idx: FuncIdx) -> None:
        if not self.has_function(idx):
            raise ValidationError(
                f"Function index outside of valid range: {idx} >= {len(self.functions)}"
            )

    def has_function(self, idx: FuncIdx) -> bool:
        return idx < len(self.functions)

    def get_function(self, idx: FuncIdx) -> FunctionType:
        return self.functions[idx]

    #
    # Tables
    #
    def validate_table_idx(self, idx: TableIdx) -> None:
        if not self.has_table(idx):
            raise ValidationError(
                f"Table index outside of valid range: {idx} >= {len(self.tables)}"
            )

    def has_table(self, idx: TableIdx) -> bool:
        return idx < len(self.tables)

    def get_table(self, idx: TableIdx) -> TableType:
        return self.tables[idx]

    #
    # Memory
    #
    def validate_mem_idx(self, idx: MemoryIdx) -> None:
        if not self.has_mem(idx):
            raise ValidationError(
                f"Memory index outside of valid range: {idx} >= {len(self.mems)}"
            )

    def has_mem(self, idx: MemoryIdx) -> bool:
        return idx < len(self.mems)

    def get_mem(self, idx: MemoryIdx) -> MemoryType:
        return self.mems[idx]

    #
    # Global
    #
    def validate_global_idx(self, idx: GlobalIdx) -> None:
        if not self.has_global(idx):
            raise ValidationError(
                f"Global index outside of valid range: {idx} >= {len(self.globals)}"
            )

    def has_global(self, idx: GlobalIdx) -> bool:
        return idx < len(self.globals)

    def get_global(self, idx: GlobalIdx) -> GlobalType:
        return self.globals[idx]

    #
    # Locals
    #
    def validate_local_idx(self, idx: LocalIdx) -> None:
        if not self.has_local(idx):
            raise ValidationError(
                f"Locals index outside of valid range: {idx} >= {len(self.locals)}"
            )

    def has_local(self, idx: LocalIdx) -> bool:
        return idx < len(self.locals)

    def get_local(self, idx: LocalIdx) -> ValType:
        return self.locals[idx]


class Context(BaseContext):
    def __init__(self,
                 *,
                 types: Tuple[FunctionType, ...],
                 functions: Tuple[FunctionType, ...],
                 tables: Tuple[TableType, ...],
                 mems: Tuple[MemoryType, ...],
                 globals: Tuple[GlobalType, ...],
                 locals: Tuple[ValType, ...],
                 labels: Tuple[ValType, ...],
                 # `returns` may be `None`, but the argument must be
                 # explicitely supplied.
                 returns: Union[None, Tuple[ValType, ...]],
                 ) -> None:
        self.types = types
        self.functions = functions
        self.tables = tables
        self.mems = mems
        self.globals = globals
        self.locals = locals
        self.labels = labels
        self.returns = returns

    def copy(self,
             *,
             types: Tuple[FunctionType, ...] = None,
             functions: Tuple[FunctionType, ...] = None,
             tables: Tuple[TableType, ...] = None,
             mems: Tuple[MemoryType, ...] = None,
             globals: Tuple[GlobalType, ...] = None,
             locals: Tuple[ValType, ...] = None,
             labels: Tuple[ValType, ...] = None,
             returns: Tuple[ValType, ...] = None) -> 'Context':
        return type(self)(
            types=types or self.types,
            functions=functions or self.functions,
            tables=tables or self.tables,
            mems=mems or self.mems,
            globals=globals or self.globals,
            locals=locals or self.locals,
            labels=labels or self.labels,
            returns=returns or self.returns,
        )

    def expression_context(self,
                           *,
                           types: Tuple[FunctionType, ...] = None,
                           functions: Tuple[FunctionType, ...] = None,
                           tables: Tuple[TableType, ...] = None,
                           mems: Tuple[MemoryType, ...] = None,
                           globals: Tuple[GlobalType, ...] = None,
                           locals: Tuple[ValType, ...] = None,
                           labels: Tuple[ValType, ...] = None,
                           returns: Tuple[ValType, ...] = None) -> 'ExpressionContext':
        context = self.copy(
            types=types,
            functions=functions,
            tables=tables,
            mems=mems,
            globals=globals,
            locals=locals,
            labels=labels,
            returns=returns,
        )
        return ExpressionContext(context)


class ExpressionContext(BaseContext):
    _operand_stack: Optional[OperandStack]
    _control_stack: Optional[ControlStack]
    _result_type: Optional[Tuple[ValType, ...]] = None

    def __init__(self, context: Context) -> None:
        self.is_final = False
        self._operand_stack = OperandStack()
        self._control_stack = ControlStack()

        # context properties
        self.types = context.types
        self.functions = context.functions
        self.tables = context.tables
        self.mems = context.mems
        self.globals = context.globals
        self.locals = context.locals
        self.labels = context.labels
        self.returns = context.returns

    #
    # Validation data structures
    #
    @property
    def operand_stack(self) -> OperandStack:
        if self._operand_stack is None:
            raise AttributeError(
                "The `operand_stack` is not available on a finialized "
                "ExpressionContext"
            )
        return self._operand_stack

    @property
    def control_stack(self) -> ControlStack:
        if self._control_stack is None:
            raise AttributeError(
                "The `control_stack` is not available on a finialized "
                "ExpressionContext"
            )
        return self._control_stack

    @property
    def result_type(self) -> Tuple[ValType, ...]:
        if not self.is_final:
            raise AttributeError(
                "Result type is not available until the `ExpressionContext` has "
                "been finalized."
            )
        elif self._result_type is None:
            raise Exception("Invariant")
        else:
            return self._result_type

    #
    # Context manager API
    #
    def __enter__(self) -> 'ExpressionContext':
        if self.is_final:
            raise ValidationError(
                "This `ExpressionContext` has already been finalized."
            )
        return self

    def __exit__(self, exc_type: None, exc_value: None, traceback: None) -> None:
        if exc_type is None:
            self._decomission()

    def _decomission(self) -> None:
        if self.is_final:
            raise ValidationError(
                "This `ExpressionContext` has already been finalized."
            )
        self._result_type = tuple(self.operand_stack)
        self._operand_stack = None
        self._control_stack = None
        self.is_final = True

    #
    # Validation API
    #
    def mark_unreachable(self) -> None:
        """
        Mark the current frame as unreachable.
        """
        frame = self.control_stack.pop()
        while len(self.operand_stack) > frame.height:
            self.operand_stack.pop()
        self.control_stack.push(frame.mark_unreachable())

    def push_control_frame(self,
                           label_types: Tuple[ValType, ...],
                           end_types: Tuple[ValType, ...]) -> None:
        """
        Mark the entry into a new control frame (such as encountering a BLOCK or IF instruction)
        """
        frame = ControlFrame(label_types, end_types, len(self.operand_stack), False)
        self.control_stack.push(frame)

    def pop_control_frame(self) -> ControlFrame:
        try:
            frame = self.control_stack.peek()
        except IndexError:
            raise ValidationError("Attempt to pop from empty control stack")

        self.pop_operands_of_expected_types(frame.end_types)

        if len(self.operand_stack) != frame.height:
            raise ValidationError(
                f"Operand stack height invalid.  Expected: {frame.height}  Got: "
                f"{len(self.operand_stack)}"
            )
        return self.control_stack.pop()

    def pop_operand(self) -> Operand:
        frame = self.control_stack.peek()

        if frame.is_unreachable and len(self.operand_stack) == frame.height:
            return Unknown
        elif len(self.operand_stack) <= frame.height:
            raise ValidationError(
                f"Underflow: Insufficient operands: {len(self.operand_stack)} <= "
                f"{frame.height}"
            )
        else:
            return self.operand_stack.pop()

    def pop_operand_and_assert_type(self, expected: Operand) -> Operand:
        actual = self.pop_operand()

        if actual is Unknown or expected is Unknown:
            return expected
        elif actual == expected:
            return actual
        else:
            raise ValidationError(
                f"Type mismatch on operand stack.  Expected: {expected}  Got: "
                f"{actual}"
            )

    def pop_operands_of_expected_types(self,
                                       expected_types: Tuple[ValType, ...],
                                       ) -> None:
        for expected in reversed(expected_types):
            self.pop_operand_and_assert_type(expected)
