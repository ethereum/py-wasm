import pytest

from wasm.datatypes import (
    Store,
)
from wasm.execution import (
    Configuration,
    Frame,
    Label,
)


@pytest.fixture
def config():
    return Configuration(Store())


def mk_frame():
    return Frame(module=None, locals=[], instructions=[], arity=0)


def mk_label():
    return Label(arity=0, instructions=[], is_loop=False)


def test_configuration_frame_stack_size(config):
    assert len(config._frame_stack) == 0

    frame_a = mk_frame()
    config.push_frame(frame_a)

    assert len(config._frame_stack) == 1

    frame_b = mk_frame()
    config.push_frame(frame_b)

    assert len(config._frame_stack) == 2

    assert config.pop_frame() is frame_b
    assert config.pop_frame() is frame_a

    assert len(config._frame_stack) == 0


def test_configuration_has_active_frame(config):
    assert config.has_active_frame is False

    frame_a = mk_frame()
    config.push_frame(frame_a)

    assert config.has_active_frame is True

    config.pop_frame()

    assert config.has_active_frame is False


def test_configuration_frame_property(config):
    assert not hasattr(config, 'frame')

    frame_a = mk_frame()
    config.push_frame(frame_a)

    assert config._frame is frame_a

    frame_b = mk_frame()
    config.push_frame(frame_b)

    assert config._frame is frame_b

    assert config.pop_frame() is frame_b

    assert config._frame is frame_a


def test_configuration_has_active_label(config):
    assert config.has_active_label is False

    frame_a = mk_frame()
    config.push_frame(frame_a)

    assert config.has_active_label is False

    label_a = mk_label()
    config.push_label(label_a)

    assert config.has_active_label is True

    # now push a new frame and there should not be an active label
    frame_b = mk_frame()
    config.push_frame(frame_b)

    assert config.has_active_label is False

    # now pop the frame and should have an active label
    config.pop_frame()

    assert config.has_active_label is True

    config.pop_label()

    assert config.has_active_label is False


def test_configuration_cannot_pop_frame_with_active_label(config):
    assert config.has_active_label is False

    frame_a = mk_frame()
    config.push_frame(frame_a)

    assert config.has_active_label is False

    label_a = mk_label()
    config.push_label(label_a)

    assert config.has_active_label is True

    with pytest.raises(ValueError):
        config.pop_frame()


def test_configuration_instructions_property(config):
    assert not hasattr(config, '_instructions')

    frame_a = mk_frame()
    config.push_frame(frame_a)

    assert config._instructions is frame_a.instructions

    label_a = mk_label()
    config.push_label(label_a)

    assert config._instructions is label_a.instructions

    frame_b = mk_frame()
    config.push_frame(frame_b)

    assert config._instructions is frame_b.instructions

    label_b = mk_label()
    config.push_label(label_b)

    assert config._instructions is label_b.instructions

    label_c = mk_label()
    config.push_label(label_c)

    assert config._instructions is label_c.instructions


def test_configuration_push_and_pop_from_operand_stack(config):
    with pytest.raises(AttributeError):
        config.push_operand(0)

    frame_a = mk_frame()
    config.push_frame(frame_a)

    assert config.operand_stack_size == 0

    config.push_operand(0)
    config.push_operand(1)
    config.push_operand(2)
    config.push_operand(3)
    config.push_operand(4)
    config.push_operand(5)

    assert config.operand_stack_size == 6

    assert config.pop_operand() == 5
    assert config.operand_stack_size == 5
    assert config.pop2_operands() == (4, 3)
    assert config.operand_stack_size == 3
    assert config.pop3_operands() == (2, 1, 0)
    assert config.operand_stack_size == 0


def test_configuration_push_and_pop_u32_from_operand_stack(config):
    with pytest.raises(AttributeError):
        config.push_operand(0)

    frame_a = mk_frame()
    config.push_frame(frame_a)

    config.push_operand(0)
    config.push_operand(1)
    config.push_operand(2)
    config.push_operand(3)
    config.push_operand(4)
    config.push_operand(5)

    assert config.pop_u32() == 5
    assert config.pop2_u32() == (4, 3)
    assert config.pop3_u32() == (2, 1, 0)


def test_configuration_push_and_pop_u64_from_operand_stack(config):
    with pytest.raises(AttributeError):
        config.push_operand(0)

    frame_a = mk_frame()
    config.push_frame(frame_a)

    config.push_operand(0)
    config.push_operand(1)
    config.push_operand(2)
    config.push_operand(3)
    config.push_operand(4)
    config.push_operand(5)

    assert config.pop_u64() == 5
    assert config.pop2_u64() == (4, 3)
    assert config.pop3_u64() == (2, 1, 0)


def test_configuration_get_label_by_idx(config):
    with pytest.raises(AttributeError):
        config.push_operand(0)

    frame = mk_frame()
    config.push_frame(frame)

    label_3 = mk_label()
    config.push_label(label_3)
    label_2 = mk_label()
    config.push_label(label_2)
    label_1 = mk_label()
    config.push_label(label_1)
    label_0 = mk_label()
    config.push_label(label_0)

    assert config.get_label_by_idx(0) is label_0
    assert config.get_label_by_idx(1) is label_1
    assert config.get_label_by_idx(2) is label_2
    assert config.get_label_by_idx(3) is label_3

    with pytest.raises(IndexError):
        assert config.get_label_by_idx(4)
