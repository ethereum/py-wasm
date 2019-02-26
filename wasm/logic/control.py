import logging
from typing import (
    Tuple,
    cast,
)

from wasm.datatypes import (
    FunctionAddress,
    FunctionInstance,
    HostFunction,
    LabelIdx,
)
from wasm.exceptions import (
    Exhaustion,
    Trap,
)
from wasm.execution import (
    Configuration,
    Frame,
    Label,
)
from wasm.instructions import (
    Block,
    Br,
    BrIf,
    BrTable,
    Call,
    CallIndirect,
    If,
    Loop,
)
from wasm.typing import (
    TValue,
)

logger = logging.getLogger('wasm.logic.control')


def unreachable_op(config: Configuration) -> None:
    """
    Logic function for the UNREACHABLE opcode
    """
    if config.enable_logic_fn_logging:
        logger.debug("%s()", config.instructions.current.opcode.text)
    raise Trap("TRAP")


def nop_op(config: Configuration) -> None:
    """
    Logic function for the NOP opcode
    """
    if config.enable_logic_fn_logging:
        logger.debug("%s()", config.instructions.current.opcode.text)


def block_op(config: Configuration) -> None:
    """
    Logic function for the BLOCK opcode
    """
    block = cast(Block, config.instructions.current)

    if config.enable_logic_fn_logging:
        logger.debug("%s()", block.opcode.text)

    label = Label(
        arity=len(block.result_type),
        instructions=block.instructions,
        is_loop=False,
    )
    config.push_label(label)


def loop_op(config: Configuration) -> None:
    """
    Logic function for the LOOP opcode
    """
    instruction = cast(Loop, config.instructions.current)

    if config.enable_logic_fn_logging:
        logger.debug("%s()", instruction.opcode.text)

    label = Label(
        arity=0,
        instructions=instruction.instructions,
        is_loop=True,
    )
    config.push_label(label)


def if_op(config: Configuration) -> None:
    """
    Logic function for the IF opcode
    """
    instruction = cast(If, config.instructions.current)

    if config.enable_logic_fn_logging:
        logger.debug("%s()", instruction.opcode.text)

    value = config.pop_operand()
    arity = len(instruction.result_type)

    if value:
        label = Label(
            arity=arity,
            instructions=instruction.instructions,
            is_loop=False,
        )
    else:
        label = Label(
            arity=arity,
            instructions=instruction.else_instructions,
            is_loop=False,
        )

    config.push_label(label)


def _exit_block(config: Configuration) -> None:
    """
    Helper function for when the control flow for a label exits.
    """
    label = config.pop_label()
    config.extend_operands(label.operand_stack)


def _return_from_function(config: Configuration) -> None:
    """
    Helper function for when the control flow for a frame exits.
    """
    valn = tuple(config.pop_operand() for _ in range(config.frame.arity))
    # discard all of the current labels before popping the frame.
    while config.has_active_label:
        config.pop_label()
    config.pop_frame()

    if config.has_active_frame:
        config.extend_operands(valn)
    else:
        config.extend_results(valn)


def else_op(config: Configuration) -> None:
    """
    Logic function for the ELSE opcode
    """
    if config.enable_logic_fn_logging:
        logger.debug("%s()", config.instructions.current.opcode.text)

    _exit_block(config)


def end_op(config: Configuration) -> None:
    """
    Logic function for the END opcode
    """
    if config.enable_logic_fn_logging:
        logger.debug("%s()", config.instructions.current.opcode.text)

    if config.has_active_label:
        _exit_block(config)
    elif config.has_active_frame:
        _return_from_function(config)
    else:
        raise Exception("Invariant?")


def _br(config: Configuration, label_idx: LabelIdx) -> None:
    """
    Helper function for the BR, BR_IF, and BR_TABLE opcodes.
    """
    label = config.get_by_label_idx(label_idx)
    # take any return values off of the stack before popping labels
    valn = tuple(config.pop_operand() for _ in range(label.arity))

    if label.is_loop:
        # For loops we keep the label which represents the loop on the stack
        # since the continuation of a loop is beginning back at the beginning
        # of the loop itself.
        for _ in range(label_idx):
            config.pop_label()
        config.instructions.seek(0)
    else:
        for _ in range(label_idx + 1):
            config.pop_label()

    # put return values back on the stack.
    config.extend_operands(valn)


def br_op(config: Configuration) -> None:
    """
    Logic function for the BR opcode
    """
    instruction = cast(Br, config.instructions.current)

    if config.enable_logic_fn_logging:
        logger.debug("%s()", instruction.opcode.text)

    _br(config, instruction.label_idx)


def br_if_op(config: Configuration) -> None:
    """
    Logic function for the BR_IF opcode
    """
    if config.enable_logic_fn_logging:
        logger.debug("%s()", config.instructions.current.opcode.text)

    value = config.pop_operand()

    if value:
        instruction = cast(BrIf, config.instructions.current)
        _br(config, instruction.label_idx)


def br_table_op(config: Configuration) -> None:
    """
    Logic function for the BR_TABLE opcode
    """
    instruction = cast(BrTable, config.instructions.current)

    if config.enable_logic_fn_logging:
        logger.debug("%s()", instruction.opcode.text)

    label_indices = instruction.label_indices
    default_label_idx = instruction.default_idx

    idx = config.pop_operand()

    if idx < len(label_indices):
        label_idx = label_indices[int(idx)]
        _br(config, label_idx)
    else:
        _br(config, default_label_idx)


def return_op(config: Configuration) -> None:
    """
    Logic function for the RETURN opcode
    """
    if config.enable_logic_fn_logging:
        logger.debug("%s()", config.instructions.current.opcode.text)

    _return_from_function(config)


def _setup_call(config: Configuration, function_address: FunctionAddress) -> None:
    """
    Helper function used when entering a new frame during execution.
    """
    function = config.store.funcs[function_address]
    function_args = tuple(reversed([
        config.pop_operand()
        for _ in range(len(function.type.params))
    ]))
    _setup_function_invocation(config, function_address, function_args)


def _setup_function_invocation(config: Configuration,
                               function_address: FunctionAddress,
                               function_args: Tuple[TValue, ...]) -> None:
    """
    Helper function for invoking a function by the function's address.
    """
    if config.frame_stack_size > 1024:
        # TODO: this is not part of spec, but this is required to pass tests.
        # Tests pass with limit 10000, maybe more
        raise Exhaustion("Function length greater than 1024")

    function = config.store.funcs[function_address]

    if len(function_args) != len(function.type.params):
        raise TypeError(
            f"Wrong number of arguments. Expected {len(function.type.params)} "
            f"Got {len(function_args)}"
        )

    if isinstance(function, FunctionInstance):
        locals = [valtype.zero for valtype in function.code.locals]
        frame = Frame(
            module=function.module,
            locals=list(function_args) + locals,
            # TODO: do we need this wrapping anymore?
            instructions=Block.wrap_with_end(function.type.results, function.code.body),
            arity=len(function.type.results),
        )
        config.push_frame(frame)
    elif isinstance(function, HostFunction):
        ret = function.hostcode(config, function_args)
        if len(ret) > 1:
            raise Exception("Invariant")
        elif ret:
            config.push_operand(ret[0])
    else:
        raise Exception("Invariant: unreachable code path")


def call_op(config: Configuration) -> None:
    """
    Logic function for the CALL opcode
    """
    instruction = cast(Call, config.instructions.current)

    if config.enable_logic_fn_logging:
        logger.debug("%s()", instruction.opcode.text)

    function_address = config.frame.module.func_addrs[instruction.function_idx]
    _setup_call(config, function_address)


def call_indirect_op(config: Configuration) -> None:
    """
    Logic function for the CALL_INDIRECT opcode
    """
    instruction = cast(CallIndirect, config.instructions.current)

    if config.enable_logic_fn_logging:
        logger.debug("%s()", instruction.opcode.text)

    table_address = config.frame.module.table_addrs[0]
    table = config.store.tables[table_address]
    function_type = config.frame.module.types[instruction.type_idx]

    element_idx = config.pop_u32()

    if len(table.elem) <= element_idx:
        raise Trap("Element index out of table range: {element_idx} > {len(table.elem)}")

    function_address = table.elem[element_idx]

    if function_address is None:
        raise Trap("Table element at index {element_idx} is empty")

    function = config.store.funcs[int(function_address)]

    if function.type != function_type:
        raise Trap("Function type mismatch.  Expected {function_type}.  Got {function.type}")

    _setup_call(config, function_address)
