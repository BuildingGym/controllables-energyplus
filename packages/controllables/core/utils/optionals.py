r"""
TODO
"""


from typing import Callable, TypeVar, Optional


_T = TypeVar('_T')


def optional(value: Optional[_T], default_func: Callable[[], _T]) -> _T:
    """
    Returns the provided value if it's not :class:`None`, 
    otherwise returns the result of the default function.
    
    :param value: The value to check.
    :param default_func: The default value generator.
    :return: :param:`value` if it's not :class:`None`, 
        otherwise the result of :param:`default_func`.
    """

    return value if value is not None else default_func()


__all__ = [
    'optional',
]