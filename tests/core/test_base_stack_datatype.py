import pytest

from wasm.stack import (
    BaseStack,
)


class StackForTesting(BaseStack[str]):
    pass


@pytest.fixture
def stack():
    return StackForTesting()


def test_stack_pushing_and_popping(stack):
    stack.push('a')
    stack.push('b')
    stack.push('c')
    stack.push('d')
    stack.push('e')

    assert stack.pop() == 'e'
    assert stack.pop() == 'd'
    assert stack.pop() == 'c'
    assert stack.pop() == 'b'
    assert stack.pop() == 'a'


def test_stack_pop2(stack):
    stack.push('a')
    stack.push('b')
    stack.push('c')
    stack.push('d')

    assert stack.pop2() == ('d', 'c')
    assert stack.pop2() == ('b', 'a')


def test_stack_pop3(stack):
    stack.push('a')
    stack.push('b')
    stack.push('c')
    stack.push('d')
    stack.push('e')
    stack.push('f')

    assert stack.pop3() == ('f', 'e', 'd')
    assert stack.pop3() == ('c', 'b', 'a')


def test_stack_peek(stack):
    stack.push('a')
    assert stack.peek() == 'a'

    stack.push('b')
    assert stack.peek() == 'b'

    stack.pop()

    assert stack.peek() == 'a'


def test_stack_length(stack):
    assert len(stack) == 0

    stack.push('a')
    stack.push('b')

    assert len(stack) == 2


def test_stack_bool_casting(stack):
    assert not stack

    stack.push('a')

    assert stack

    stack.pop()

    assert not stack


def test_stack_iterable_casting(stack):
    stack.push('a')
    stack.push('b')
    stack.push('c')

    assert tuple(stack) == ('a', 'b', 'c')
