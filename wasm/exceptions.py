class BaseWasmException(Exception):
    pass


class MalformedModule(BaseWasmException):
    pass


class InvalidModule(BaseWasmException):
    pass


class TrapError(BaseWasmException):
    pass


class Exhaustion(BaseWasmException):
    pass


class Unlinkable(BaseWasmException):
    pass
