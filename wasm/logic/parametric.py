import logging

from wasm.execution import (
    Configuration,
)

logger = logging.getLogger('wasm.logic.parametric')


def drop_op(config: Configuration) -> None:
    """
    Logic functin for the DROP opcode.
    """
    if config.enable_logic_fn_logging:
        logger.debug("%s()", config.instructions.current.opcode.text)

    config.pop_operand()


def select_op(config: Configuration) -> None:
    """
    Logic functin for the SELECT opcode.
    """
    if config.enable_logic_fn_logging:
        logger.debug("%s()", config.instructions.current.opcode.text)

    a, b, c = config.pop3_operands()

    if a:
        config.push_operand(c)
    else:
        config.push_operand(b)
