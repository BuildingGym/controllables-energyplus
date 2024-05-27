# from __future__ import annotations

import builtins as _builtins_
import typing as _typing_
import operator as _operator_
import functools as _functools_


# TODO ref https://stackoverflow.com/a/46328797
def zip(*mappings: _typing_.Mapping):
    keys_sets = _builtins_.map(_builtins_.set, mappings)
    common_keys = _functools_.reduce(_builtins_.set.intersection, keys_sets)
    for key in common_keys:
        yield (key, _builtins_.tuple(_builtins_.map(_operator_.itemgetter(key), mappings)))


# TODO
def group(
    iterable: _typing_.Iterable, 
    keyfunc: _typing_.Callable[[_typing_.Any], _typing_.Any] | None = None,
) -> _typing_.Mapping:
    keyfunc = keyfunc if keyfunc is not None else (lambda x: x)
    res = dict()
    for element in iterable:
        res.setdefault(keyfunc(element), list()).append(element)
    return res


#from .. import utils as _utils_



import collections as _collections_

# TODO _utils_.ipy.html.DictView
class GroupView(_collections_.UserDict):
    pass


class GroupableIterator:
    # TODO do not consume!!!!
    def __init__(self, iterable: _typing_.Iterable):
        self._iter = iterable

    def __iter__(self):
        return self._iter.__iter__()

    def group(self, keyfunc):
        return GroupView({
            key: (
                self.__class__(iterable=value) 
                if isinstance(value, _typing_.Iterable) else 
                value
            )
            for key, value in 
            group(self._iter, keyfunc=keyfunc).items()
        })
    

__all__ = [
    'zip',
    'group',
    'GroupView',
    'GroupableIterator',
]