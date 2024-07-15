r"""
TODO
"""


import abc as _abc_
from typing import Generic, TypeVar


# TODO doc
class RefManager(
    _abc_.ABC, 
    Generic[_RefT := TypeVar('_RefT')],
):
    @_abc_.abstractmethod
    def __getitem__(self, ref: _RefT):
        ...


__all__ = [
    'RefManager',
]
