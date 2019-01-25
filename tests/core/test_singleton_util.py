from wasm._utils.singleton import (
    Singleton,
)


def test_base_singleton_class():
    inst_a = Singleton()
    inst_b = Singleton()

    assert inst_a is inst_b


class SubA(Singleton):
    pass


class SubB(Singleton):
    pass


def test_subclassed_singletons():
    base = Singleton()

    inst_a1 = SubA()
    inst_a2 = SubA()

    inst_b1 = SubB()
    inst_b2 = SubB()

    assert inst_a1 is inst_a2
    assert inst_b1 is inst_b2

    assert base is not inst_a1
    assert base is not inst_b1
    assert inst_a1 is not inst_b1


class WithArgs(Singleton):
    def __init__(self, val_a, val_b):
        self.val_a = val_a
        self.val_b = val_b


def test_singleton_class_with_initialization_args():
    inst_a = WithArgs(1, val_b='2')
    inst_b = WithArgs(1, val_b='2')

    assert inst_a is inst_b

    assert inst_a.val_a == 1
    assert inst_a.val_b == '2'
