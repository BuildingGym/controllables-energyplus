r"""
Variables.
"""


import abc as _abc_
from typing import (
    Any, 
    Callable, 
    Generic, 
    Iterable, 
    Literal,
    Mapping,
    ParamSpec,
    TypeAlias,
    TypeVar,
)

from .callbacks import (
    BaseCallback, 
    BaseCallbackManager,
    CallbackManager,
)
from .refs import RefT, BaseRefManager


_ValT = TypeVar('_ValT')


class NilType(type):
    r"""
    :class:`NoneType`-like metaclass for representing nil values.
    """

    pass

class Nil(metaclass=NilType):
    r"""
    :class:`None`-like class for representing nil values.
    """
    
    pass


class BaseVariable(
    _abc_.ABC, 
    Generic[_ValT],
):
    r"""
    Variable base class.
    """

    # TODO stdize!!!!!
    events: BaseCallbackManager[
        Literal['change'],
        BaseCallback,
    ] | None = None
    r"""
    Events associated with this variable.

    TODO :class:`Observable`?
    """

    @property
    @_abc_.abstractmethod
    def value(self) -> _ValT | Nil:
        r"""
        Get the value of this variable.

        :return: The value of this variable.
        """

        ...


class BaseMutableVariable(
    BaseVariable[_ValT], 
    _abc_.ABC,
    Generic[_ValT],
):
    r"""Mutable variable base class."""

    @BaseVariable.value.setter
    @_abc_.abstractmethod
    def value(self, o: _ValT | Nil):
        r"""
        Set the value of this variable.

        :param o: The value to set.
        """

        ...


VarT = TypeVar('VarT', bound=BaseVariable)


# TODO generics?
class BaseVariableManager(
    Generic[RefT, VarT],
    BaseRefManager[RefT, VarT],
    _abc_.ABC,
):
    r"""
    Variable manager base class.
    """

    @_abc_.abstractmethod
    def __contains__(self, ref: RefT) -> bool:
        r"""
        Check if a variable is enabled.

        :param ref: Reference to the variable.
        :return: Whether the variable is enabled.
        """

        ...

    @_abc_.abstractmethod
    def __getitem__(self, ref: RefT) -> VarT:
        r"""
        Access a variable by its reference.

        :param ref: Reference to the variable to be accessed.
        :return: Variable associated with reference `ref`.
        """

        ...

    @_abc_.abstractmethod
    def __delitem__(self, ref: RefT) -> None:
        r"""
        Delete a variable by its reference.
        Implementation shall remove access to the variable,
        and release any resources associated with the variable, 
        if necessary.

        :param ref: Reference to the variable to be disabled.
        """

        ...



import functools as _functools_

from .utils.mappers import BaseMapper, CollectionMapper


# TODO typing
class BaseCompositeVariable(
    BaseVariable,
    _abc_.ABC,
    #Generic[T := TypeVar('T')], 
):
    r"""
    Composite variable base class.
    This can serve as a container for one or multiple variables.
    When used with one variable, it behaves like a proxy 
    for the underlying variable.
    """

    # TODO typehint: CompositeTypes[BaseVariable]
    # TODO
    def __mapper__(self, next_mapper: 'BaseMapper'):
        r"""
        The mapper for the composite variable.
        This defines how the elements of the composite variable
        can be discovered and accessed.
        TODO FIXME(clarity) By default, this assumes non-composite variables.

        :param next_mapper: The next mapper to be applied.
        """
        
        return next_mapper

    __variables__: Any
    r"""
    The variables contained in this composite variable.
    Permissible types determined by :attr:`__mapper__`.

    .. note:: This MUST be overridden in subclasses.
    """

    @_functools_.cached_property
    def events(self):
        # TODO
        m = CallbackManager()

        @self.__mapper__
        def setup(o):
            if not isinstance(o, BaseVariable):
                return
            if o.events is None:
                return
            if 'change' in o.events:
                o.events['change'].on(m['change'])
        setup(self.__variables__)

        return m

    @property
    def value(self):
        @self.__mapper__
        def get(o):
            return o.value if isinstance(o, BaseVariable) else o
        return get(self.__variables__)


class BaseMutableCompositeVariable(
    BaseCompositeVariable, 
    BaseMutableVariable,
    _abc_.ABC,
):
    r"""
    The mutable version of :class:`BaseCompositeVariable`.
    """

    @property
    def value(self):
        return super().value

    @value.setter
    def value(self, o):
        @self.__mapper__
        def set(o, val):
            if isinstance(o, BaseVariable):
                o.value = val
                return val
            # TODO raise?
            return None
        return set(self.__variables__, o)


class Variable(
    Generic[_ValT],
    BaseVariable[_ValT], 
    _abc_.ABC,
):
    def __init__(self, value: _ValT):
        r"""
        Initialize the variable.

        :param value: The initial value of the variable.
        """

        super().__init__()
        self.__value__ = value

    @property
    def value(self):
        return self.__value__


class MutableVariable(
    Generic[_ValT],
    Variable[_ValT],
    _abc_.ABC,
):
    class EventManager(CallbackManager):
        def __contains__(self, ref):
            return ref in ('change', )

    @_functools_.cached_property
    def events(self):
        return self.EventManager()

    @property
    def value(self):
        return super().value    

    @value.setter
    def value(self, o: _ValT):
        self.__value__ = o
        # TODO !!!!!
        self.events['change']()


# TODO typing
class CompositeVariable(
    BaseCompositeVariable,
    _abc_.ABC,
):
    r"""
    TODO
    """

    # TODO !!!!!
    def __mapper__(self, next_mapper):
        return CollectionMapper(next_mapper=next_mapper)

    def __init__(self, variables: Any):
        self.__variables__ = variables

    
class MutableCompositeVariable(
    BaseMutableCompositeVariable,
    CompositeVariable, 
    BaseMutableVariable,
):
    r"""
    TODO
    """

    pass


# TODO events
# TODO metaclass=VariableProxyMeta
class ComputedVariable(
    BaseVariable[_ValT],
    Generic[_ParamT := ParamSpec('_ParamT', bound=BaseVariable | Any), _ValT],
):
    r"""
    TODO update when any of `BaseVariable` passed is updated!!!!

    .. code-block:: python
        vars: BaseVariableManager = ...
        ComputedVariable(
            lambda a, b: a.value + b.value, 
            a=vars['a'], b=vars['b'],
        )
    """

    # TODO necesito?
    @classmethod
    def from_operator(
        cls, 
        operator: Callable[_ParamT, _ValT], 
        *args: _ParamT.args, 
        **kwargs: _ParamT.kwargs,
    ):
        # TODO
        def valueof(o: BaseVariable | Any):
            return o.value if isinstance(o, BaseVariable) else o

        def operator_(*args, **kwargs):
            return operator(
                *(valueof(o) for o in args), 
                **{k: valueof(v) for k, v in kwargs.items()},
            )
        
        return cls(operator_, *args, **kwargs)

    def __init__(
        self, 
        func: Callable[_ParamT, _ValT], 
        *args: _ParamT.args, 
        **kwargs: _ParamT.kwargs,
    ):
        self.__func__ = func
        self.__args__ = args
        self.__kwargs__ = kwargs

    @property
    def value(self):
        return self.__func__(*self.__args__, **self.__kwargs__)


class ValueProxyMeta(type(BaseVariable)):
    def __new__(
        cls, name, bases, namespace, 
        proxy_attrs: Iterable[str] | Mapping[str, str] = [],
        **kwargs,
    ):
        r"""TODO docs"""

        def make_method(attr):
            def method(self, *args, **kwargs):
                class ProxyComputedVariable(
                    ComputedVariable, 
                    metaclass=ValueProxyMeta, 
                    proxy_attrs=proxy_attrs,
                ): 
                    pass
                return ProxyComputedVariable.from_operator(
                    lambda self_v, *args, **kwargs:
                        getattr(self_v, attr)(*args, **kwargs), 
                    self, *args, **kwargs,
                )
            return method
        
        proxy_attrs_ = (
            dict(proxy_attrs)
            if isinstance(proxy_attrs, Mapping) else 
            dict(zip(proxy_attrs, proxy_attrs))
        )

        for proxy_attr, attr in proxy_attrs_.items():
            namespace[proxy_attr] = make_method(attr)

        return super().__new__(
            cls, 
            name, bases, namespace,
            **kwargs,
        )


from . import utils as _utils_


class VariableNumOpsMixin(
    BaseVariable,
    metaclass=ValueProxyMeta,
    proxy_attrs=(
        *_utils_.attrs.numeric.BINARY,
        *_utils_.attrs.numeric.RBINARY,
        *_utils_.attrs.numeric.UNARY,
    ),
):
    r"""TODO"""

    pass


class VariableNumArrayOpsMixin(
    BaseVariable,
):
    r"""TODO"""

class VariableContainerOpsMixin(
    BaseVariable,
    metaclass=ValueProxyMeta,
    # TODO
    proxy_attrs=(
        '__getitem__',
    )
):
    r"""TODO"""


# TODO valueof()? Iterator => StreamVariable?


__all__ = [
    'BaseVariable',
    'BaseMutableVariable',
    'BaseVariableManager',
    'Variable',
    'MutableVariable',
    'VariableNumOpsMixin',
]
