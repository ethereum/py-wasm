class BaseWasmException(Exception):
    pass


class Malformed(BaseWasmException):
    pass


class Invalid(BaseWasmException):
    pass


class Trap(BaseWasmException):
    pass


class Exhaustion(BaseWasmException):
    pass


class Unlinkable(BaseWasmException):
    pass
