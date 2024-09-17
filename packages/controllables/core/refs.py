r"""
Specs for reference-related operations.
"""


import abc as _abc_
from typing import Any, Callable, Generic, TypeAlias, TypeVar


RefT = TypeVar('RefT')
ValT = TypeVar('ValT')


# TODO
Derefable: TypeAlias = RefT | Any | Callable[['BaseRefManager'], RefT]
r"""
Any type that can be dereferenced.

.. seealso:: :func:`deref`
"""


class BaseRefManager(
    _abc_.ABC, 
    Generic[RefT, ValT],
):
    r"""
    Reference manager base class.
    """

    @_abc_.abstractmethod
    def __getitem__(self, ref: RefT) -> ValT:
        r"""
        Retrieve the value of a reference.

        :param ref: The reference.
        :return: The value of the reference.
        """

        ...

    @_abc_.abstractmethod
    def __contains__(self, ref: RefT) -> bool:
        r"""
        Check if a reference exists in this manager.

        :param ref: The reference.
        :return: Whether the reference exists.
        """

        ...


def deref(manager: BaseRefManager, ref: Derefable[RefT]) -> ValT:
    r"""
    Dereference a reference using the provided reference manager.

    :param manager: The reference manager.
    :param ref: The reference.
    :return: The dereferenced value.
    :raises TypeError: If any of the below occur:
        * reference NOT exists in the manager provided,
        * reference NOT as specified in :var:`Derefable`.
    """

    if ref in manager:
        return manager[ref]
    
    if isinstance(ref, Callable):
        return ref(manager)
    
    raise TypeError(
        f'Invalid/non-existent reference: {ref}; '
        f'Expected to return any of: '
        f'* {manager!r}[{ref!r}] iff {ref!r} in {manager!r}, '
        f'* {ref!r}({manager!r})'
    )


__all__ = [
    'RefT',
    'ValT',
    'Derefable',
    'BaseRefManager',
    'deref',
]
