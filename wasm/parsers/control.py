from typing import (
    IO,
    Iterable,
    Tuple,
    cast,
)

from wasm._utils.toolz import (
    partitionby,
)
from wasm.instructions import (
    BaseInstruction,
    Block,
    Br,
    BrIf,
    BrTable,
    Call,
    CallIndirect,
    Else,
    End,
    If,
    Instruction,
    Loop,
    Nop,
    Return,
    Unreachable,
)
from wasm.opcodes import (
    BinaryOpcode,
)

from .blocks import (
    parse_blocktype,
)
from .indices import (
    parse_function_idx,
    parse_label_idx,
    parse_type_idx,
)
from .null import (
    parse_null_byte,
)
from .vector import (
    parse_vector,
)


def parse_control_instruction(opcode: BinaryOpcode,
                              stream: IO[bytes]) -> Instruction:
    """
    Parse one of the Control instructions from the stream
    """
    if opcode is BinaryOpcode.UNREACHABLE:
        return Unreachable()
    elif opcode is BinaryOpcode.NOP:
        return Nop()
    elif opcode is BinaryOpcode.BLOCK:
        return parse_block_instruction(stream)
    elif opcode is BinaryOpcode.LOOP:
        return parse_loop_instruction(stream)
    elif opcode is BinaryOpcode.IF:
        return parse_if_instruction(stream)
    elif opcode is BinaryOpcode.BR:
        return parse_br_instruction(stream)
    elif opcode is BinaryOpcode.BR_IF:
        return parse_br_if_instruction(stream)
    elif opcode is BinaryOpcode.BR_TABLE:
        return parse_br_table_instruction(stream)
    elif opcode is BinaryOpcode.RETURN:
        return Return()
    elif opcode is BinaryOpcode.CALL:
        return parse_call_instruction(stream)
    elif opcode is BinaryOpcode.CALL_INDIRECT:
        return parse_call_indirect_instruction(stream)
    elif opcode is BinaryOpcode.END:
        return End()
    elif opcode is BinaryOpcode.ELSE:
        return Else()
    else:
        raise Exception(f"Unhandled: {opcode}")


def parse_block_instruction(stream: IO[bytes]) -> Block:
    """
    Parser for the BLOCK instruction
    """
    result_type = parse_blocktype(stream)
    instructions = parse_inner_block_instructions(stream)

    return Block(result_type, instructions)


def parse_inner_block_instructions(stream: IO[bytes]) -> Tuple[BaseInstruction, ...]:
    """
    Helper to parse the instruction sequence for a BLOCK instruction
    """
    return tuple(_parse_inner_block_instructions(stream))


def _parse_inner_block_instructions(stream: IO[bytes]) -> Iterable[BaseInstruction]:
    # recursive parsing
    from wasm.parsers.instructions import parse_instruction  # noqa: F401

    while True:
        instruction = cast(BaseInstruction, parse_instruction(stream))
        yield instruction
        if isinstance(instruction, End):
            break


def parse_loop_instruction(stream: IO[bytes]) -> Loop:
    """
    Parser for the LOOP instruction
    """
    result_type = parse_blocktype(stream)
    instructions = parse_inner_block_instructions(stream)

    return Loop(result_type, instructions)


def parse_if_instruction(stream: IO[bytes]) -> If:
    """
    Parser for the IF instruction
    """
    result_type = parse_blocktype(stream)

    all_instructions = parse_inner_block_instructions(stream)
    partitioned_instructions = tuple(partitionby(lambda v: isinstance(v, Else), all_instructions))

    if len(partitioned_instructions) == 1:  # if without else
        if_instructions = all_instructions
        instructions = if_instructions[:-1] + Else.as_tail()
        else_instructions = End.as_tail()
    elif len(partitioned_instructions) == 2:  # empty if clause
        instructions, else_instructions = partitioned_instructions
    elif len(partitioned_instructions) == 3:
        if_instructions, _, else_instructions = partitioned_instructions
        instructions = if_instructions + Else.as_tail()
    else:
        raise Exception("TODO: if block contained more than one else clause")

    return If(
        result_type,
        instructions,
        else_instructions,
    )


def parse_br_instruction(stream: IO[bytes]) -> Br:
    """
    Parser for the BR instruction
    """
    label = parse_label_idx(stream)
    return Br(label)


def parse_br_if_instruction(stream: IO[bytes]) -> BrIf:
    """
    Parser for the BR_IF instruction
    """
    label = parse_label_idx(stream)
    return BrIf(label)


def parse_br_table_instruction(stream: IO[bytes]) -> BrTable:
    """
    Parser for the BR_TABLE instruction
    """
    labels = parse_vector(parse_label_idx, stream)
    default_label = parse_label_idx(stream)

    return BrTable(labels, default_label)


def parse_call_instruction(stream: IO[bytes]) -> Call:
    """
    Parser for the CALL instruction
    """
    function_idx = parse_function_idx(stream)
    return Call(function_idx)


def parse_call_indirect_instruction(stream: IO[bytes]) -> CallIndirect:
    """
    Parser for the CALL_INDIRECT instruction
    """
    type_idx = parse_type_idx(stream)
    parse_null_byte(stream)

    return CallIndirect(type_idx)
