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
    instruction = cast(LocalOp, config.instructions.current)
    logger.debug("%s()", config.instructions.current.opcode.text)

    value = config.pop_operand()
    config.frame.locals[instruction.local_idx] = value


def get_local_op(config: Configuration) -> None:
    instruction = cast(LocalOp, config.instructions.current)
    logger.debug("%s()", config.instructions.current.opcode.text)

    value = config.frame.locals[instruction.local_idx]
    config.push_operand(value)


def tee_local_op(config: Configuration) -> None:
    instruction = cast(LocalOp, config.instructions.current)
    logger.debug("%s()", config.instructions.current.opcode.text)

    value = config.pop_operand()
    config.frame.locals[instruction.local_idx] = value
    config.push_operand(value)


def get_global_op(config: Configuration) -> None:
    instruction = cast(GlobalOp, config.instructions.current)
    logger.debug("%s()", config.instructions.current.opcode.text)

    global_address = config.frame.module.global_addrs[instruction.global_idx]
    global_ = config.store.globals[global_address]
    # TODO: remove runtime assertion
    assert isinstance(global_.value, global_.valtype.value)
    config.push_operand(global_.value)


def set_global_op(config: Configuration) -> None:
    instruction = cast(GlobalOp, config.instructions.current)
    logger.debug("%s()", config.instructions.current.opcode.text)

    global_address = config.frame.module.global_addrs[instruction.global_idx]
    global_ = config.store.globals[global_address]
    if global_.mut is not Mutability.var:
        raise Exception("Attempt to set immutable global")
    value = config.pop_operand()
    config.store.globals[global_address] = GlobalInstance(global_.valtype, value, global_.mut)
