
import builtins as _builtins_

import typing as _typing_
import abc as _abc_

# TODO
from .... import utils as _utils_


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
                for index, subobjs in _utils_.mappings.zip(*objs)
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
    'BaseMapper',
    'StructureMapper',
]