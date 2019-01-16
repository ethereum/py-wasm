class BaseWasmException(Exception):
    pass


class MalformedModule(BaseWasmException):
    pass


class InvalidModule(BaseWasmException):
    pass


class Trap(BaseWasmException):
    """
    https://webassembly.github.io/spec/core/bikeshed/index.html#trap
    """
    pass


class Exhaustion(BaseWasmException):
    pass


class Unlinkable(BaseWasmException):
    pass
