r"""
Specs for reference-related operations.
"""


import abc as _abc_
from typing import Container, Callable, Generic, Mapping, TypeAlias, Type, TypeVar


RefT = TypeVar('RefT')
ValT = TypeVar('ValT')

Derefable: TypeAlias = Callable[['ProtoRefManager'], RefT] | RefT
r"""
Any type that can be dereferenced.

.. seealso:: :func:`deref`
"""


class ProtoRefManager(
    _abc_.ABC, 
    #Mapping[RefT, ValT],
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


# TODO
class BaseRefManager(
    ProtoRefManager[RefT, ValT],
    _abc_.ABC, 
    Generic[RefT, ValT],
):
    __ref_slots__: Container | None = None

    def __contains__(self, ref):
        if self.__ref_slots__ is None:
            return False
        return ref in self.__ref_slots__


def deref(
    manager: ProtoRefManager[RefT, ValT] | None, 
    ref: Derefable[RefT],
) -> ValT:
    r"""
    Dereference a reference using the provided reference manager.

    :param manager: The reference manager.
    :param ref: The reference.
    :return: The dereferenced value.
    :raises TypeError: 
        If reference NOT exists in the manager provided,
        -OR- :class:`callable` as specified in :var:`Derefable`.
    """

    if manager is not None and ref in manager:
        return manager[ref]
    
    if isinstance(ref, Callable):
        return ref(manager)
    
    raise TypeError(
        f'Invalid/non-existent reference: {ref}; '
        f'Expected to return any of: '
        f'* {manager!r}[{ref!r}] iff {ref!r} in {manager!r}, '
        f'* {ref!r}({manager!r})'
    )


def bounded_deref(
    manager: ProtoRefManager[RefT, ValT] | None, 
    ref: ValT | Derefable[RefT],
    bound: Type[ValT] | tuple[Type[ValT], ...],
) -> ValT:
    r"""
    Dereference a reference using the provided reference manager 
    -AND- ensure it is of a specific type.
    If the reference is already of the specified type, it is returned as is.

    :param manager: The reference manager.
    :param ref: The reference.
    :param bound: The expected type(s) of the reference, 
        the format follows the `classinfo` argument of :func:`isinstance`.
    :return: The dereferenced value.
    :raises TypeError: 
        If reference NOT exists in the manager provided,
        -OR- the dereferenced value is NOT an instance of the specified type.
    """

    if isinstance(ref, bound):
        return ref

    res = deref(manager, ref)
    if not isinstance(res, bound):
        raise TypeError(
            f'Invalid reference value: {res!r}; '
            f'Expected to be any of: {bound!r}'
        )
    return res


__all__ = [
    'RefT',
    'ValT',
    'Derefable',
    'ProtoRefManager',
    'deref',
    'bounded_deref',
]
