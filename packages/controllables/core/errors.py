r"""
Errors.
"""


class TemporaryUnavailableError(Exception):
    r"""
    Exception raised for resources that are temporarily unavailable.

    In the scope of this package, such exception often implies that 
    a variable or an entity does not currently exist but may become
    available in the future, though not guaranteed.
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
    Warning equivalent of :class:`OptionalImportError`.
    """

    pass


__all__ = [
    'TemporaryUnavailableError',
    'OptionalModuleNotFoundError',
]