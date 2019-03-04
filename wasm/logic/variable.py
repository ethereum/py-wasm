import logging
from typing import (
    cast,
)

from wasm.datatypes import (
    GlobalInstance,
    Mutability,
)
from wasm.execution import (
    Configuration,
)
from wasm.instructions import (
    GlobalOp,
    LocalOp,
)

logger = logging.getLogger('wasm.logic.variable')


def set_local_op(config: Configuration) -> None:
    """
    Logic functin for the SET_LOCAL opcode.
    """
    instruction = cast(LocalOp, config.current_instruction)
    logger.debug("%s()", instruction.opcode.text)

    value = config.pop_operand()
    config.frame_locals[instruction.local_idx] = value


def get_local_op(config: Configuration) -> None:
    """
    Logic functin for the GET_LOCAL opcode.
    """
    instruction = cast(LocalOp, config.current_instruction)
    logger.debug("%s()", instruction.opcode.text)

    value = config.frame_locals[instruction.local_idx]
    config.push_operand(value)


def tee_local_op(config: Configuration) -> None:
    """
    Logic functin for the TEE_LOCAL opcode.
    """
    instruction = cast(LocalOp, config.current_instruction)
    logger.debug("%s()", instruction.opcode.text)

    value = config.pop_operand()
    config.frame_locals[instruction.local_idx] = value
    config.push_operand(value)


def get_global_op(config: Configuration) -> None:
    """
    Logic functin for the GET_GLOBAL opcode.
    """
    instruction = cast(GlobalOp, config.current_instruction)
    logger.debug("%s()", instruction.opcode.text)

    global_address = config.frame_module.global_addrs[instruction.global_idx]
    global_ = config.store.globals[global_address]
    config.push_operand(global_.value)


def set_global_op(config: Configuration) -> None:
    """
    Logic functin for the SET_GLOBAL opcode.
    """
    instruction = cast(GlobalOp, config.current_instruction)
    logger.debug("%s()", instruction.opcode.text)

    global_address = config.frame_module.global_addrs[instruction.global_idx]
    global_ = config.store.globals[global_address]
    if global_.mut is not Mutability.var:
        raise Exception("Attempt to set immutable global")
    value = config.pop_operand()
    config.store.globals[global_address] = GlobalInstance(global_.valtype, value, global_.mut)
