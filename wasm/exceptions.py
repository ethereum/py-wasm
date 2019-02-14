class BaseWasmException(Exception):
    """
    Base exception class for this library.
    """
    pass


class MalformedModule(BaseWasmException):
    """
    Raise during module parsing if the module is malformed for any reason
    """
    pass


class InvalidModule(BaseWasmException):
    """
    Raise during module validation if the module is invalid for any reason.
    """
    pass


class Trap(BaseWasmException):
    """
    Raise when a TRAP condition is encountered
    """
    pass


class Exhaustion(BaseWasmException):
    """
    Raise when one of the various environment specific resource limits is
    reached.
    """
    pass


class Unlinkable(BaseWasmException):
    """
    Raise during module linking if a module is unlinkable.
    """
    pass


class ValidationError(BaseWasmException):
    """
    Internal exception used during module validation to signal a validation
    failure.
    """
    pass


class ParseError(BaseWasmException):
    """
    Internal exception used during module parsing to signal a failure,
    typically due to the module being malformed.
    """
    pass
