from wasm._utils.interned import (
    Interned,
)


def test_base_interned_class():
    inst_a = Interned()
    inst_b = Interned()

    assert inst_a is inst_b


class SubA(Interned):
    pass


class SubB(Interned):
    pass


def test_subclassed_interneds():
    base = Interned()

    inst_a1 = SubA()
    inst_a2 = SubA()

    inst_b1 = SubB()
    inst_b2 = SubB()

    assert inst_a1 is inst_a2
    assert inst_b1 is inst_b2

    assert base is not inst_a1
    assert base is not inst_b1
    assert inst_a1 is not inst_b1


class WithArgs(Interned):
    def __init__(self, val_a, val_b):
        self.val_a = val_a
        self.val_b = val_b


def test_interned_class_with_initialization_args():
    obj_a = WithArgs(1, 2)
    obj_b = WithArgs(1, 2)

    assert obj_a.val_a == 1
    assert obj_a.val_b == 2
    assert obj_a is obj_b

    obj_c = WithArgs(1, 3)

    assert obj_c.val_a == 1
    assert obj_c.val_b == 3
    assert obj_c is not obj_a


def test_interned_class_discards_unrefrenced_objects():
    num_cached = len(Interned._cache)
    obj_a = SubA()

    assert len(SubA._cache) == num_cached + 1

    del obj_a

    assert len(SubA._cache) == num_cached
