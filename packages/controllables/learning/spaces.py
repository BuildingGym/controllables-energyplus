r"""
Spaces.
"""


from typing import Any, Generic, Mapping, Tuple, TypeVar

from controllables.core.errors import OptionalModuleNotFoundError
try: import gymnasium as _gymnasium_
except ModuleNotFoundError as e:
    raise OptionalModuleNotFoundError.suggest(['gymnasium']) from e
try: import numpy as _numpy_
except ModuleNotFoundError as e:
    raise OptionalModuleNotFoundError.suggest(['numpy']) from e

from controllables.core.components import (
    Component,
)
from controllables.core.variables import (
    ValT,
    BaseMutableVariable,
    BaseVariable, 
    BaseVariableManager,
)
from controllables.core.refs import (
    ProtoRefManager,
    Derefable,
    bounded_deref,
)
from controllables.core.utils.mappers import (
    BaseMapper,
    DictMapper,
    TupleMapper,    
    CompositeMapper,
)


class Space(
    Generic[
        SpaceValT := TypeVar('SpaceValT', covariant=True),
    ],
    _gymnasium_.spaces.Space[SpaceValT],
):
    r"""
    TODO doc binding

    .. seealso::
    * <https://gymnasium.farama.org/api/spaces/#gymnasium.spaces.Space>
    """

    __ref__: BaseVariable | Derefable[BaseVariable] | None = None
    r"""The bound reference."""

    __should_cast__: bool = False

    def bind(
        self, 
        ref: BaseVariable | Derefable[BaseVariable], 
        cast: bool = False,
    ):
        r"""
        Bind a reference to this space.

        :param ref: The reference to bind.
        :param cast: Whether to cast the value of the bound variable.
        :return: This space.
        """

        self.__ref__ = ref
        self.__should_cast__ = cast
        return self
    
    @property
    def ref(self):
        if self.__ref__ is None:
            raise ValueError('TODO')
        return self.__ref__
    
    def cast(self, value: SpaceValT):
        return _numpy_.array(
            value,
            dtype=self.dtype,
        ).reshape(self.shape)     

    def deref(
        self, 
        manager: ProtoRefManager[Any, BaseVariable] | None = None,
    ) -> BaseVariable:
        r"""
        Dereference the bound variable.
        
        :param manager: The reference manager to use.
        :return: The bound variable.
        """

        # TODO
        return bounded_deref(
            manager, self.ref,
            bound=BaseVariable,
        )
    

class SpaceMapper(BaseMapper):
    def maps(self, *objs):
        return any(
            isinstance(obj, Space) and obj.__ref__ is not None
            for obj in objs
        )
    
    def __call__(self, *objs):
        return self.__next_mapper__(*objs)


class BoxSpace(Space, _gymnasium_.spaces.Box):
    r"""
    TODO doc
    """

    def cast(self, value):
        return _numpy_.clip(
            super().cast(value),
            self.low, self.high,
        )


class DiscreteSpace(Space, _gymnasium_.spaces.Discrete):
    pass


class SequenceSpace(Space, _gymnasium_.spaces.Sequence):
    # TODO
    pass


class DictSpace(
    Space, 
    _gymnasium_.spaces.Dict,
):
    r"""
    TODO doc
    """

    pass


class DictSpaceMapper(DictMapper):
    def maps(self, *objs):
        return all(
            isinstance(obj, (DictSpace, dict, Mapping)) 
            for obj in objs
        )

class TupleSpace(Space, _gymnasium_.spaces.Tuple):
    pass

class TupleSpaceMapper(TupleMapper):
    def maps(self, *objs):
        return all(isinstance(obj, (TupleSpace, tuple, Tuple)) for obj in objs)


class SpaceVariable(
    BaseVariable[ValT], 
    Component[ProtoRefManager[Any, BaseVariable]],
    Generic[ValT],
):
    r"""
    Variable for spaces.

    * If the associated space has a bound variable, 
    this reflects the value of the bound variable.
    * Otherwise, the space is traversed to collect
    the values of the bound variables, the structure
    of which is preserved. Supported spaces include:
        * :class:`DictSpace`
        * :class:`TupleSpace`

    .. warning::

    TODO Upon read access (of the property :attr:`value`):

    * The value of the bound variable is NOT checked against 
    the space constraints (e.g. ``low``/``high`` in :class:`BoxSpace`);
    * However, the value will be cast to the space's dtype 
    and reshaped to the space's shape.

    See below examples for details.

    .. doctest::

        >>> from controllables.core import Variable

        Use with a `fundamental space <https://gymnasium.farama.org/api/spaces/fundamental>`_:

        >>> var = SpaceVariable(
        ...     BoxSpace(low=0, high=10)
        ...     .bind(Variable(1))
        ... )
        >>> var.value
        1

        Use with a `composite space <https://gymnasium.farama.org/api/spaces/composite>`_:

        >>> var = SpaceVariable(
        ...     DictSpace({
        ...         'a': DiscreteSpace(3).bind(Variable(1)),
        ...         'b': BoxSpace(low=0, high=10).bind(Variable(2)),
        ...     })
        ... )
        >>> sorted(var.value.items())
        [('a', 1), ('b', 2)]

        Use with a `composite space <https://gymnasium.farama.org/api/spaces/composite>`_
        bound to a variable - short-circuit:

        >>> var = SpaceVariable(
        ...     DictSpace({
        ...         'a': DiscreteSpace(3),
        ...         'b': BoxSpace(low=0, high=10),
        ...     })
        ...     .bind(Variable({'a': 1, 'b': 2.}))
        ... )
        >>> var.value
        {'a': 1, 'b': 2.0}

        Use with a reference:

        >>> var = SpaceVariable(
        ...     BoxSpace(low=0, high=10)
        ...     .bind(lambda _: Variable(1))
        ... )
        >>> var.value # doctest: +ELLIPSIS
        1

        Use with a reference manager:

        >>> space = BoxSpace(low=0, high=10)
        >>> var = SpaceVariable(space.bind('x'))
        >>> var.__attach__({'x': Variable(1)})
        >>> var.value # doctest: +ELLIPSIS
        1

    .. seealso::
    :class:`SpaceVariable.Mapper`

    """

    class Mapper(CompositeMapper):
        r"""Underlying mapper for :class:`SpaceVariable`."""

        def __init__(self, next_mapper=None, mappers=[]):
            super().__init__(
                next_mapper=next_mapper,
                mappers=[
                    SpaceMapper(next_mapper),
                    DictSpaceMapper(self),
                    TupleSpaceMapper(self),
                    *mappers,
                ],
            )

    def __init__(self, space: Space):
        super().__init__()
        self.space = space

    @property
    def value(self):
        def getter(space: Space):
            # TODO check isinstance space
            res = space.deref(self.__parent__).value
            if space.__should_cast__:
                res = space.cast(res)
            return res
        return self.Mapper(getter)(self.space)


class MutableSpaceVariable(
    SpaceVariable[ValT],
    Component[ProtoRefManager[Any, BaseMutableVariable]],
    Generic[ValT],
):
    r"""
    Mutable variable for spaces.

    .. warning::

    Upon write access (of the property :attr:`value`):

    * The value will be passed to the bound variable as-is.

    See the below example for details.

    .. doctest::

        >>> from controllables.core import MutableVariable

        >>> var_a = MutableVariable(1)
        >>> var_b = MutableVariable(2)
        >>> var = MutableSpaceVariable(
        ...     DictSpace({
        ...         'a': DiscreteSpace(3).bind(var_a),
        ...         'b': BoxSpace(low=0, high=10).bind(var_b),
        ...     })
        ... )
        >>> var.value = {'a': 2, 'b': 3.}
        >>> var_a.value, var_b.value
        (2, 3.0)
        >>> sorted(var.value.items()) # doctest: +ELLIPSIS
        [('a', 2), ('b', 3.0)]

    """

    @SpaceVariable.value.setter
    def value(self, v):
        def setter(space: Space, v: Any):
            if space.__should_cast__:
                v = space.cast(v)
            space.deref(self.__parent__).value = v
        return self.Mapper(setter)(self.space, v)
    

__all__ = [
    'BoxSpace',
    'DiscreteSpace',
    'DictSpace',
    #'SequenceSpace',
    'TupleSpace',
    'SpaceVariable',
    'MutableSpaceVariable',
]