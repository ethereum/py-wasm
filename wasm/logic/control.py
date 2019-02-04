from typing import (
    cast,
)

from wasm.exceptions import (
    Trap,
)
from wasm.execution import (
    Configuration,
    Label,
)
from wasm.instructions import (
    Block,
)


def unreachable_op(config: Configuration) -> None:
    raise Trap("TRAP")


def nop_op(config: Configuration) -> None:
    pass


def block_op(config: Configuration) -> None:
    block = cast(Block, config.instructions.current)

    label = Label(
        arity=len(block.result_type),
        instructions=block.instructions,
        is_loop=False,
    )
    config.push_label(label)
