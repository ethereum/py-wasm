from collections.abc import (
    Sequence,
)
from typing import (
    Iterable,
    Iterator,
    Tuple,
    overload,
)

from wasm.instructions import (
    BaseInstruction,
)


class InstructionSequence(Sequence):
    """
    Stateful stream of instructions for web assembly execution.
    """
    _instructions: Tuple[BaseInstruction, ...]

    def __init__(self, instructions: Iterable[BaseInstruction]) -> None:
        self._instructions = tuple(instructions)
        self._idx = -1

    def __str__(self) -> str:
        return f"[{' > '.join((str(instr) for instr in self._instructions))}]"

    def __repr__(self) -> str:
        return f"InstructionSequence({str(self)})"

    def __len__(self) -> int:
        return len(self._instructions)

    def __next__(self) -> BaseInstruction:
        self._idx += 1
        try:
            return self._instructions[self._idx]
        except IndexError:
            raise StopIteration

    def __iter__(self) -> Iterator[BaseInstruction]:
        while self._idx < len(self._instructions) - 1:
            yield next(self)

    @overload
    def __getitem__(self, idx: int) -> BaseInstruction:
        pass

    @overload  # noqa: 811
    def __getitem__(self, s: slice) -> 'InstructionSequence':
        pass

    def __getitem__(self, item):  # noqa: F811
        if isinstance(item, int):
            return self._instructions[item]
        elif isinstance(item, slice):
            return type(self)(self._instructions[item])
        else:
            raise TypeError(f"Unsupported key type: {type(item)}")

    @property
    def pc(self) -> int:
        return max(0, self._idx)

    @pc.setter
    def pc(self, value: int) -> None:
        self.seek(value)

    @property
    def current(self) -> BaseInstruction:
        return self[self.pc]

    def seek(self, idx: int) -> None:
        self._idx = idx - 1
