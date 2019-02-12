import contextlib
from typing import (
    Iterator,
)

import numpy


@contextlib.contextmanager
def no_overflow() -> Iterator[None]:
    old_settings = numpy.seterr(over='raise')

    try:
        yield
    finally:
        numpy.seterr(**old_settings)


@contextlib.contextmanager
def allow_overflow() -> Iterator[None]:
    old_settings = numpy.seterr(over='ignore')

    try:
        yield
    finally:
        numpy.seterr(**old_settings)


@contextlib.contextmanager
def allow_underflow() -> Iterator[None]:
    old_settings = numpy.seterr(under='ignore')

    try:
        yield
    finally:
        numpy.seterr(**old_settings)


@contextlib.contextmanager
def allow_zerodiv() -> Iterator[None]:
    old_settings = numpy.seterr(divide='ignore')

    try:
        yield
    finally:
        numpy.seterr(**old_settings)


@contextlib.contextmanager
def allow_invalid() -> Iterator[None]:
    old_settings = numpy.seterr(invalid='ignore')

    try:
        yield
    finally:
        numpy.seterr(**old_settings)


@contextlib.contextmanager
def allow_multiple(*,
                   over: bool = None,
                   under: bool = None,
                   divide: bool = None,
                   invalid: bool = None) -> Iterator[None]:
    old_settings = numpy.seterr(
        over='ignore' if over is not None else None,
        under='ignore' if under is not None else None,
        divide='ignore' if divide is not None else None,
        invalid='ignore' if invalid is not None else None,
    )

    try:
        yield
    finally:
        numpy.seterr(**old_settings)
