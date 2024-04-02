from __future__ import annotations

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


from .. import utils as _utils_



import collections as _collections_

# TODO
class GroupView(_utils_.ipy.html.DictView, _collections_.UserDict):
    pass


class GroupableIterator:
    # TODO do not consume!!!!
    def __init__(self, iterable: _typing_.Iterable):
        self._iter = iterable

    def __iter__(self):
        return self._iter
    
    def list(self):
        return list(self._iter)

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
    

    



import typing as _typing_
import abc as _abc_


class BaseMapper(_abc_.ABC):
    @_abc_.abstractmethod
    def __call__(
        self, 
        *objs: _typing_.Any,
    ) -> _typing_.Any:
        raise NotImplementedError

# TODO
# TODO generics [T, TransT]
class StructureMapper(BaseMapper):
    _struct_types: _typing_.Mapping[_typing_.Callable, _typing_.Tuple[_typing_.Type]] = {
        # mappings
        _builtins_.dict: (_builtins_.dict, ),
        # collections
        _builtins_.tuple: (_builtins_.tuple, ),
        _builtins_.list: (_builtins_.list, ),
        _builtins_.set: (_builtins_.set, ),
    }

    def __init__(self, mapper_base: BaseMapper | None = None):
        super().__init__()
        self._mapper_base = mapper_base

    def __call__(
        self, 
        *objs: _typing_.Any, 
    ):
        isinstance_it = lambda it, cls: all(
            isinstance(el, cls) for el in it
        )

        for map_cls in (_builtins_.dict, ):
            if not isinstance_it(objs, self._struct_types[map_cls]):
                continue
            return map_cls(
                (index, self.__call__(*subobjs))
                for index, subobjs in zip(*objs)
            )

        for coll_cls in (_builtins_.tuple, _builtins_.list, _builtins_.set):
            if not isinstance_it(objs, self._struct_types[coll_cls]):
                continue
            return coll_cls(
                self.__call__(*subobjs)
                for subobjs in _builtins_.zip(*objs)
            )

        if self._mapper_base is not None:
            return self._mapper_base(*objs)

        raise TypeError(f'Type of objects unknown, got {objs}')


__all__ = [
    zip,
    group,
    GroupableIterator,
    BaseMapper,
    StructureMapper,
]