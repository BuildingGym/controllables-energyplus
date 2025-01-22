r"""
Error definitions.
"""


class TemporaryUnavailableError(Exception):
    r"""
    Exception raised for resources that are temporarily unavailable.

    In the scope of this package, such exception often implies that 
    a variable or an entity does not currently exist but may become
    available in the future, though not guaranteed.
    """

    def warning(self, *args, **kwargs):
        r"""
        Convert this exception to a warning.
        """

        return TemporaryUnavailableWarning(*self.args, *args, **kwargs)


class TemporaryUnavailableWarning(RuntimeWarning):
    r"""
    Warning equivalent of :class:`TemporaryUnavailableError`.
    """

    pass


import sys as _sys_
from typing import Collection

class OptionalModuleNotFoundError(ModuleNotFoundError):
    r"""
    Exception raised when an optional dependency/module is not found.
    """

    @classmethod
    def suggest(cls, package_names: Collection[str]):
        return cls(
            'Missing optional dependency(ies)/module(s), run: '
            f'''`{_sys_.executable} -m pip install {
                str.join(' ', (f'"{s}"' for s in package_names))}`'''
        )
    
class OptionalModuleNotFoundWarning(RuntimeWarning, OptionalModuleNotFoundError):
    r"""
    Warning equivalent of :class:`OptionalModuleNotFoundError`.
    """

    pass


import abc as _abc_

class ExceptionableMixin(_abc_.ABC):
    __exc__: BaseException | None = None

    def err(self, exc: BaseException):
        self.__exc__ = exc

    def throw(self):
        if self.__exc__ is not None:
            exc = self.__exc__
            self.__exc__ = None
            raise exc


__all__ = [
    'TemporaryUnavailableError',
    'TemporaryUnavailableWarning',
    'OptionalModuleNotFoundError',
    'OptionalModuleNotFoundWarning',
    'ExceptionableMixin'
]