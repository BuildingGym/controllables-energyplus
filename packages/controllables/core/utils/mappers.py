r"""
TODO 
"""


import abc as _abc_
from typing import (
    Generic, 
    Protocol, 
    TypeAlias, 
    TypeVar, 
    runtime_checkable,
)

from .zippers import zip_iterable, zip_mapping


@runtime_checkable
class MapperFunction(
    Generic[
        InT := TypeVar('InT'), 
        OutT := TypeVar('OutT'),
    ],
    Protocol,
):
    @_abc_.abstractmethod
    def __call__(self, *objs: InT) -> OutT:
        r"""
        Transform the input objects.

        :param *objs: The objects to transform. TODO NOTE
        :return: The transformed objects.
        :raises TypeError: If the input objects are not supported.
        """

        ...


class BaseMapper(
    Generic[
        InT := TypeVar('InT'), 
        OutT := TypeVar('OutT'),
    ],
    MapperFunction[InT, OutT],
    _abc_.ABC,
):
    r"""
    Base class for :func:`builtins.map`-like mappers.
    This standardizes the interface for mapping functions 
    that operate on custom data types.
    """

    _MapperTypes: TypeAlias = '''
        BaseMapper[Any, OutT] 
        | MapperFunction[Any, OutT] 
        | None
    '''

    __next_mapper__: _MapperTypes
    r"""
    The next mapper to use for elements of the input objects.
    """

    def __init__(self, next_mapper: _MapperTypes = None):
        r"""
        Initialize the mapper.

        :param next_mapper: 
            The next mapper to use.

        .. seealso:: :attr:`__next_mapper__`
        """

        super().__init__()
        self.__next_mapper__ = next_mapper

    @property
    def next_mapper(self) -> 'BaseMapper':
        return MapperProxy(self.__next_mapper__)

    @_abc_.abstractmethod
    def maps(self, *objs: InT) -> bool:
        r"""
        Check if the input objects can be mapped.

        :param *objs: The objects to check.
        :return: Whether the objects can be mapped.
        """

        ...

    def _ensure_maps(self, *objs: InT) -> None:
        r"""
        Ensure that the input objects can be mapped.

        :param *objs: The objects to check.
        :raises TypeError: If the input objects are not supported.
        """

        if self.maps(*objs):
            return
        raise TypeError(
            f'Type of objects unknown: '
            f'got {list(type(o) for o in objs)} (content: {objs})'
        )


class MapperProxy(BaseMapper):
    def maps(self, *objs):
        if self.__next_mapper__ is None:
            return False
        if isinstance(self.__next_mapper__, BaseMapper):
            return self.__next_mapper__.maps(*objs)
        if isinstance(self.__next_mapper__, MapperFunction):
            return True
        raise TypeError(self.__next_mapper__)
    
    def __call__(self, *objs):
        if self.__next_mapper__ is None:
            raise ValueError(
                f'No mappers present for {objs}'
            )
        if isinstance(self.__next_mapper__, MapperFunction):
            return self.__next_mapper__.__call__(*objs)
        raise TypeError(self.__next_mapper__)


from typing import Any, Callable, Mapping, Dict, Type, Iterable, Iterator

def isallinstance(it: tuple, cls: Any | tuple[Any]) -> bool:
    return all(isinstance(el, cls) for el in it)


class MappingMapper(BaseMapper[Mapping, Dict]):
    def maps(self, *objs):
        return isallinstance(objs, (dict, Mapping, ))

    def __call__(self, *objs):
        self._ensure_maps(*objs)
        return dict(
            (index, self.next_mapper(*subobjs))
            for index, subobjs in zip_mapping(*objs)
        )


class IterableMapper(BaseMapper[Iterable, Iterator]):
    def maps(self, *objs):
        return isallinstance(objs, (Iterable, ))
    
    def __call__(self, *objs):
        self._ensure_maps(*objs)
        return iter(
            self.next_mapper(*subobjs)
            for subobjs in zip_iterable(*objs)
        )
    

class CompositeMapper(MapperProxy):
    def __init__(
        self, 
        next_mapper: BaseMapper | None = None,
        mappers: Iterable[BaseMapper] = [],
    ):
        super().__init__(next_mapper=next_mapper)
        self._mappers = list(mappers)

    def add(self, *mappers: BaseMapper):
        self._mappers.extend(mappers)

    def maps(self, *objs):
        return any(
            mapper.maps(*objs) 
            for mapper in self._mappers
        ) or super().maps(*objs)
    
    def __call__(self, *objs):    
        self._ensure_maps(*objs)
        for mapper in self._mappers:
            if not mapper.maps(*objs):
                continue
            return mapper(*objs)
        return super().__call__(*objs)


from typing import Tuple, List, Set

class DictMapper(MappingMapper):
    pass

class TupleMapper(IterableMapper):
    def maps(self, *objs):
        return isallinstance(objs, (tuple, Tuple))
    
    def __call__(self, *objs):
        return tuple(super().__call__(*objs))
    
class ListMapper(IterableMapper):
    def maps(self, *objs):
        return isallinstance(objs, (list, List))
    
    def __call__(self, *objs):
        return list(super().__call__(*objs))
    
class SetMapper(IterableMapper):
    def maps(self, *objs):
        return isallinstance(objs, (set, Set))
    
    def __call__(self, *objs):
        return set(super().__call__(*objs))

class CollectionMapper(CompositeMapper):
    def __init__(self, next_mapper: BaseMapper | None = None):
        super().__init__(next_mapper=next_mapper)
        self.add(
            DictMapper(self),
            TupleMapper(self),
            ListMapper(self),
            SetMapper(self),
        )


__all__ = [
    'BaseMapper',
    'MappingMapper',
    'IterableMapper',
    'CompositeMapper',
    'DictMapper',
    'TupleMapper',
    'ListMapper',
    'SetMapper',
    'CollectionMapper',
]
