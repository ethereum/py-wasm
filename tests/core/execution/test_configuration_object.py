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


def test_configuration_frame_stack_size(config):
    assert config.frame_stack_size == 0

    frame_a = Frame(None, [], [], 0)
    config.push_frame(frame_a)

    assert config.frame_stack_size == 1

    frame_b = Frame(None, [], [], 0)
    config.push_frame(frame_b)

    assert config.frame_stack_size == 2

    assert config.pop_frame() is frame_b
    assert config.pop_frame() is frame_a

    assert config.frame_stack_size == 0


def test_configuration_has_active_frame(config):
    assert config.has_active_frame is False

    frame_a = Frame(None, [], [], 0)
    config.push_frame(frame_a)

    assert config.has_active_frame is True

    config.pop_frame()

    assert config.has_active_frame is False


def test_configuration_frame_property(config):
    with pytest.raises(IndexError):
        config.frame

    frame_a = Frame(None, [], [], 0)
    config.push_frame(frame_a)

    assert config.frame is frame_a

    frame_b = Frame(None, [], [], 0)
    config.push_frame(frame_b)

    assert config.frame is frame_b

    assert config.pop_frame() is frame_b

    assert config.frame is frame_a


def test_configuration_has_active_label(config):
    assert config.has_active_label is False

    frame_a = Frame(None, [], [], 0)
    config.push_frame(frame_a)

    assert config.has_active_label is False

    label_a = Label(0, [], False)
    config.push_label(label_a)

    assert config.has_active_label is True

    # now push a new frame and there should not be an active label
    frame_b = Frame(None, [], [], 0)
    config.push_frame(frame_b)

    assert config.has_active_label is False

    # now pop the frame and should have an active label
    config.pop_frame()

    assert config.has_active_label is True

    config.pop_label()

    assert config.has_active_label is False


def test_configuration_active_label_property(config):
    with pytest.raises(IndexError):
        config.active_label

    frame_a = Frame(None, [], [], 0)
    config.push_frame(frame_a)

    with pytest.raises(IndexError):
        config.active_label

    label_a = Label(0, [], False)
    config.push_label(label_a)

    assert config.active_label is label_a

    label_b = Label(0, [], False)
    config.push_label(label_b)

    assert config.active_label is label_b

    # now push a new frame and there should not be an active label
    frame_b = Frame(None, [], [], 0)
    config.push_frame(frame_b)

    with pytest.raises(IndexError):
        config.active_label

    label_c = Label(0, [], False)
    config.push_label(label_c)

    assert config.active_label is label_c


def test_configuration_instructions_property(config):
    with pytest.raises(IndexError):
        config.instructions

    frame_a = Frame(None, [], [], 0)
    config.push_frame(frame_a)

    assert config.instructions is frame_a.instructions

    label_a = Label(0, [], False)
    config.push_label(label_a)

    assert config.instructions is label_a.instructions

    frame_b = Frame(None, [], [], 0)
    config.push_frame(frame_b)

    assert config.instructions is frame_b.instructions

    label_b = Label(0, [], False)
    config.push_label(label_b)

    assert config.instructions is label_b.instructions

    label_c = Label(0, [], False)
    config.push_label(label_c)

    assert config.instructions is label_c.instructions


def test_configuration_push_and_pop_from_operand_stack(config):
    with pytest.raises(IndexError):
        config.push_operand(0)

    frame_a = Frame(None, [], [], 0)
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
    with pytest.raises(IndexError):
        config.push_operand(0)

    frame_a = Frame(None, [], [], 0)
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
    with pytest.raises(IndexError):
        config.push_operand(0)

    frame_a = Frame(None, [], [], 0)
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
    with pytest.raises(IndexError):
        config.push_operand(0)

    frame = Frame(None, [], [], 0)
    config.push_frame(frame)

    label_3 = Label(0, [], False)
    config.push_label(label_3)
    label_2 = Label(0, [], False)
    config.push_label(label_2)
    label_1 = Label(0, [], False)
    config.push_label(label_1)
    label_0 = Label(0, [], False)
    config.push_label(label_0)

    assert config.get_by_label_idx(0) is label_0
    assert config.get_by_label_idx(1) is label_1
    assert config.get_by_label_idx(2) is label_2
    assert config.get_by_label_idx(3) is label_3

    with pytest.raises(IndexError):
        assert config.get_by_label_idx(4)
