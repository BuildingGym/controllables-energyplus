import builtins as _builtins_

import typing as _typing_
import abc as _abc_

# TODO rm
#from .... import utils as _utils_






def IterableZipper(*iterables: _typing_.Iterable):
    return _builtins_.zip(*iterables)

import operator as _operator_
import functools as _functools_
# TODO ref https://stackoverflow.com/a/46328797
def MappingZipper(*mappings: _typing_.Mapping):
    keys_sets = _builtins_.map(_builtins_.set, mappings)
    common_keys = _functools_.reduce(_builtins_.set.intersection, keys_sets)
    for key in common_keys:
        yield (key, _builtins_.tuple(_builtins_.map(_operator_.itemgetter(key), mappings)))



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
                for index, subobjs in MappingZipper(*objs)
            )

        for coll_cls in (_builtins_.tuple, _builtins_.list, _builtins_.set):
            if not isinstance_it(objs, self._struct_types[coll_cls]):
                continue
            return coll_cls(
                self.__call__(*subobjs)
                for subobjs in IterableZipper(*objs)
            )

        if self._mapper_base is not None:
            return self._mapper_base(*objs)

        raise TypeError(f'Type of objects unknown, got {objs}')


__all__ = [
    'BaseMapper',
    'StructureMapper',
]