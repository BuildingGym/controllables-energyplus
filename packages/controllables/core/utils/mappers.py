r"""
TODO 
"""


import abc as _abc_
import builtins as _builtins_
import typing as _typing_

from .zippers import IterableZipper, MappingZipper


class BaseMapper(_abc_.ABC):
    r"""
    Base class for :func:`builtins.map`-like mappers.
    This standardizes the interface for mapping functions 
    that operate on custom data types.
    """

    @_abc_.abstractmethod
    def __call__(
        self, 
        *objs: _typing_.Any,
    ) -> _typing_.Any:
        r"""
        Transform the input objects.
        """

        ...

# TODO typing
# TODO generics [T, TransT]
class StructureMapper(BaseMapper):
    r"""
    :func:`builtins.map`-like mapper for structured data types.
    "Structured" refers to objects composed of 
    multiple, primitive elements, such as mappings and collections.
    
    .. seealso::
        * https://foldoc.org/aggregate+type
        * https://wikipedia.org/wiki/Composite_data_type
    """

    _struct_types: _typing_.Mapping[
        _typing_.Callable[[], _typing_.Any], 
        _typing_.Tuple[_typing_.Type],
    ] = {
        # mappings
        _builtins_.dict: (_builtins_.dict, _typing_.Mapping, ),
        # collections
        _builtins_.tuple: (_builtins_.tuple, _typing_.Tuple, ),
        _builtins_.list: (_builtins_.list, _typing_.List,),
        _builtins_.set: (_builtins_.set, _typing_.Set, ),
    }
    r"""
    Supported structured types keyed by their constructors.

    This is used to make the mapper "structurally aware," such that
    it knows how to discover the primitive elements of a structured object
    and transform them accordingly using :attr:`_base_mapper`.
    
    .. note::
        * The supported key fields shall be of built-in types.
            Only mappings and collections are supported by default.
        * Override the value fields to add support for custom structured types.
    """

    def __init__(self, base_mapper: BaseMapper | None = None):
        r"""
        Initialize the mapper.

        :param base_mapper: 
            The base mapper to use for any types 
            other than the specified structured types
            in :attr:`_struct_types`.
        """

        super().__init__()
        self._base_mapper = base_mapper

    def __call__(
        self, 
        *objs: _typing_.Iterable | _typing_.Mapping | _typing_.Any, 
    ):
        r"""
        Map the input objects.

        :param *objs: The objects to map. Rules follow:

            * All objects shall of the same type, bearing the same structure.
            * Objects of different lengths are truncated to the shortest length.
            * Non-structured objects are passed to :attr:`_base_mapper`.
            * Mapping applies ONLY to values, not keys or indices.
        
        :return: The mapped object.
        """

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

        if self._base_mapper is not None:
            return self._base_mapper(*objs)

        raise TypeError(
            f'Type of objects unknown: '
            f'expected any of {list(self._struct_types)}, '
            f'got {list(type(o) for o in objs)} (content: {objs})'
        )


__all__ = [
    'BaseMapper',
    'StructureMapper',
]