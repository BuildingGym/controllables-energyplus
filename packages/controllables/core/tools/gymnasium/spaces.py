r"""
Spaces.
"""


from typing import Any, Generic, Mapping, Tuple, TypeVar

from ...errors import OptionalModuleNotFoundError
try: import gymnasium as _gymnasium_
except ModuleNotFoundError as e:
    raise OptionalModuleNotFoundError.suggest(['gymnasium']) from e
try: import numpy as _numpy_
except ModuleNotFoundError as e:
    raise OptionalModuleNotFoundError.suggest(['numpy']) from e

from ...components import (
    BaseComponent,
)
from ...variables import (
    BaseVariable, 
    BaseVariableManager,
    VariableNumOpsMixin,
    VariableNumArrayOpsMixin,
    VariableContainerOpsMixin,
)
from ...refs import (
    BaseRefManager,
    Derefable,
    deref,
)
from ...utils.mappers import (
    DictMapper,
    TupleMapper,    
    CompositeMapper,
    # TODO mv?
    isallinstance,
)


class Space(
    Generic[T := TypeVar('T', covariant=True)],
    _gymnasium_.spaces.Space[T],
):
    # TODO default None
    __ref__: BaseVariable | Derefable[BaseVariable] | None

    def bind(self, ref: Derefable[BaseVariable]):
        self.__ref__ = ref
        return self

    def deref(self, manager: BaseRefManager | None = None) -> BaseVariable:
        # TODO
        if self.__ref__ is None:
            raise ValueError('TODO')
        return (
            self.__ref__ 
            if isinstance(self.__ref__, BaseVariable) else 
            deref(manager, self.__ref__)
        )


class BoxSpace(Space, _gymnasium_.spaces.Box):
    pass


class DiscreteSpace(Space, _gymnasium_.spaces.Discrete):
    pass


class SequenceSpace(Space, _gymnasium_.spaces.Sequence):
    pass


# TODO support passthru?? (use DictSpace.__ref__ when present??)
class DictSpace(Space, _gymnasium_.spaces.Dict):
    pass

class DictSpaceMapper(DictMapper):
    def maps(self, *objs):
        # TODO map(lambda x: x.__ref__ is not None, objs)
        return isallinstance(objs, (DictSpace, dict, Mapping, ))
    

class TupleSpace(Space, _gymnasium_.spaces.Tuple):
    pass

class TupleSpaceMapper(TupleMapper):
    def maps(self, *objs):
        return isallinstance(objs, (TupleSpace, tuple, Tuple, ))    
    

class SpaceCompositeMapper(CompositeMapper):
    def __init__(self, next_mapper=None, mappers=[]):
        super().__init__(
            next_mapper=next_mapper,
            mappers=[
                DictSpaceMapper(self),
                TupleSpaceMapper(self),
                *mappers,
            ],
        )


class SpaceVariable(
    VariableNumOpsMixin,
    VariableNumArrayOpsMixin,
    VariableContainerOpsMixin,    
    BaseVariable, 
    BaseComponent[BaseVariableManager],
):
    r"""
    TODO
    """

    def __init__(self, space: Space):
        super().__init__()
        self.space = space

    @property
    def value(self):
        def getter(space: Space):
            # TODO check isinstance space
            return _numpy_.array(
                # TODO
                space.deref(self.__manager__).value,
                dtype=space.dtype,
            ).reshape(space.shape)
        return SpaceCompositeMapper(getter)(self.space)
    

class MutableSpaceVariable(SpaceVariable):
    r"""
    TODO
    """

    @SpaceVariable.value.setter
    def value(self, v):
        def setter(space: Space, v: Any):
            space.deref(self.__manager__).value = v
        return SpaceCompositeMapper(setter)(self.space, v)
    

__all__ = [
    'BoxSpace',
    'DiscreteSpace',
    'DictSpace',
    #'SequenceSpace',
    'TupleSpace',
]