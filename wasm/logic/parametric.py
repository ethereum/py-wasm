import logging

from wasm.execution import (
    Configuration,
)

logger = logging.getLogger('wasm.logic.parametric')


def drop_op(config: Configuration) -> None:
    logger.debug("%s()", config.instructions.current.opcode.text)

    config.pop_operand()


def select_op(config: Configuration) -> None:
    logger.debug("%s()", config.instructions.current.opcode.text)

    a, b, c = config.pop3_operands()

    if a:
        config.push_operand(c)
    else:
        config.push_operand(b)