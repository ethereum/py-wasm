import io
from typing import (
    Iterable,
    Tuple,
    cast,
)

from wasm._utils.toolz import (
    partitionby,
)
from wasm.datatypes import (
    ValType,
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
from wasm.typing import (
    UInt8,
)

from .indices import (
    parse_funcidx,
    parse_labelidx,
    parse_typeidx,
)
from .null import (
    parse_null_byte,
)
from .vector import (
    parse_vector,
)


def parse_control_instruction(opcode: BinaryOpcode,
                              stream: io.BytesIO) -> Instruction:
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


def parse_block_valtype(stream: io.BytesIO) -> Tuple[ValType, ...]:
    raw_byte = stream.read(1)

    if not raw_byte:
        raise Exception("TODO: end of stream")

    raw_value = UInt8(raw_byte[0])

    if raw_value == 0x40:
        return tuple()

    try:
        return (ValType.from_byte(raw_value),)
    except ValueError as err:
        raise Exception(f"TODO: parse error: invalid valtype: {err}")


def parse_block_instruction(stream: io.BytesIO) -> Block:
    result_type = parse_block_valtype(stream)
    instructions = parse_inner_block_instructions(stream)

    return Block(result_type, instructions)


def parse_inner_block_instructions(stream: io.BytesIO) -> Tuple[BaseInstruction, ...]:
    return tuple(_parse_inner_block_instructions(stream))


def _parse_inner_block_instructions(stream: io.BytesIO) -> Iterable[BaseInstruction]:
    # recursive parsing
    from wasm.parsers.instructions import parse_instruction  # noqa: F401

    while True:
        instruction = cast(BaseInstruction, parse_instruction(stream))
        yield instruction
        if isinstance(instruction, End):
            break


def parse_loop_instruction(stream: io.BytesIO) -> Loop:
    result_type = parse_block_valtype(stream)
    instructions = parse_inner_block_instructions(stream)

    return Loop(result_type, instructions)


def parse_if_instruction(stream: io.BytesIO) -> If:
    result_type = parse_block_valtype(stream)

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


def parse_br_instruction(stream: io.BytesIO) -> Br:
    label = parse_labelidx(stream)
    return Br(label)


def parse_br_if_instruction(stream: io.BytesIO) -> BrIf:
    label = parse_labelidx(stream)
    return BrIf(label)


def parse_br_table_instruction(stream: io.BytesIO) -> BrTable:
    labels = parse_vector(parse_labelidx, stream)
    default_label = parse_labelidx(stream)

    return BrTable(labels, default_label)


def parse_call_instruction(stream: io.BytesIO) -> Call:
    func_idx = parse_funcidx(stream)
    return Call(func_idx)


def parse_call_indirect_instruction(stream: io.BytesIO) -> CallIndirect:
    type_idx = parse_typeidx(stream)
    parse_null_byte(stream)

    return CallIndirect(type_idx)
