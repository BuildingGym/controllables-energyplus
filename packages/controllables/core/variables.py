r"""
Variables.
"""


import abc as _abc_
from typing import (
    Any, 
    Callable, 
    Generic, 
    Iterable, 
    Mapping,
    TypeAlias,
    TypeVar,
)


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


VariableRefType = str | Any
r"""
Reference type.

This can be a string or a reference object.
Strings shall be used as "symbols" for 
predefined shortcut variables.
"""

from .refs import BaseRefManager

# TODO generics?
class BaseVariableManager(
    BaseRefManager[VariableRefType, BaseVariable],
    _abc_.ABC,
):
    r"""
    Variable manager base class.
    """

    @_abc_.abstractmethod
    def __contains__(self, ref: VariableRefType) -> bool:
        r"""
        Check if a variable is enabled.

        :param ref: Reference to the variable.
        :return: Whether the variable is enabled.
        """

        ...

    @_abc_.abstractmethod
    def __getitem__(self, ref: VariableRefType) -> BaseVariable:
        r"""
        Access a variable by its reference.

        :param ref: Reference to the variable to be accessed.
        :return: Variable associated with reference `ref`.
        """

        ...

    @_abc_.abstractmethod
    def __delitem__(self, ref: VariableRefType) -> None:
        r"""
        Delete a variable by its reference.
        Implementation shall remove access to the variable,
        and release any resources associated with the variable, 
        if necessary.

        :param ref: Reference to the variable to be disabled.
        """

        ...



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

    @property
    def value(self):
        def getter(o):
            return o.value if isinstance(o, BaseVariable) else o
        return self.__mapper__(getter)(self.__variables__)


class BaseMutableCompositeVariable(
    BaseCompositeVariable, 
    BaseMutableVariable,
    _abc_.ABC,
):
    r"""
    TODO
    """

    @property
    def value(self):
        return super().value

    @value.setter
    def value(self, o):
        def setter(o, val):
            if isinstance(o, BaseVariable):
                o.value = val
                return val
            # TODO raise?
            return None
        return self.__mapper__(setter)(self.__variables__, o)


class Variable(
    Generic[_ValT],
    BaseVariable[_ValT], 
    _abc_.ABC,
):
    def __init__(self, value: _ValT):
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
    @Variable.value.setter
    def value(self, o: _ValT):
        self.__value__ = o


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


# TODO metaclass=VariableProxyMeta
class ComputedVariable(BaseVariable):
    r"""
    TODO update when any of `BaseVariable` passed is updated!!!!

    .. code-block:: python
        vars: BaseVariableManager = ...
        ComputedVariable(
            lambda a, b: a.value + b.value, 
            a=vars['a'], b=vars['b']
        )
    """

    @classmethod
    def from_operator(
        cls, 
        operator: Callable, 
        *args: BaseVariable | Any, 
        **kwargs: BaseVariable | Any,
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

    def __init__(self, func: Callable, *args, **kwargs):
        self._func = func
        self.__args__ = args
        self.__kwargs__ = kwargs

    @property
    def value(self):
        return self._func(*self.__args__, **self.__kwargs__)


class ValueProxyMeta(type(BaseVariable)):
    def __new__(
        cls, name, bases, namespace, 
        proxy_attrs: Iterable[str] | Mapping[str, str] = [],
        **kwargs,
    ):
        r"""TODO docs"""


        def make_method(attr):
            def method(self, *args, **kwargs):
                class ProxyComputeVariable(
                    ComputedVariable, 
                    metaclass=ValueProxyMeta, 
                    proxy_attrs=proxy_attrs,
                ): 
                    pass
                return ProxyComputeVariable.from_operator(
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


class VariableNumArrayOpsMixin(BaseVariable):
    r"""TODO"""


from typing import Iterator
from .refs import BaseRefManager

# TODO just valueof()? Iterator => StreamVariable?
class VariableRefManager(
    BaseRefManager[None | BaseVariable | Iterator, Any],
):
    r"""
    Variable reference manager.
    """

    def __contains__(self, ref):
        return isinstance(ref, (type(None), BaseVariable, Iterator))

    def __getitem__(self, ref):
        if ref is None:
            return None

        if isinstance(ref, BaseVariable):
            # TODO
            from .errors import TemporaryUnavailableError
            try: 
                return ref.value
            except TemporaryUnavailableError: 
                return None        
        
        if isinstance(ref, Iterator):
            return next(ref)

        raise TypeError(f'Unsupported reference: {ref}')


__all__ = [
    'BaseVariable',
    'BaseMutableVariable',
    'BaseVariableManager',
    'Variable',
    'MutableVariable',
    'VariableNumOpsMixin',
    'VariableRefType',
    'VariableRefManager',
]
