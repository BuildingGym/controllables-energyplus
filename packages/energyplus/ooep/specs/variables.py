r"""
Variables.
"""


import abc as _abc_
from typing import Any, Callable, TypeVar, Generic, Iterable, Mapping


_ValT = TypeVar('_ValT')

class BaseVariable(
    _abc_.ABC, 
    Generic[_ValT],
):
    r"""
    Variable base class.
    """

    @property
    @_abc_.abstractmethod
    def value(self) -> _ValT:
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
    def value(self, o: _ValT):
        r"""
        Set the value of this variable.

        :param o: The value to set.
        """
        ...

RefType = str | Any
r"""
Reference type.

This can be a string or a reference object.
Strings shall be used as "symbols" for 
predefined shortcut variables.
"""

from .refs import RefManager

# TODO generics?
class BaseVariableManager(
    RefManager[BaseVariable],
    _abc_.ABC,
):
    r"""
    Variable manager base class.
    """

    @_abc_.abstractmethod
    def __contains__(self, ref: RefType) -> bool:
        r"""
        Check if a variable is enabled.

        :param ref: Reference to the variable.
        :return: Whether the variable is enabled.
        """
        ...

    @_abc_.abstractmethod
    def __getitem__(self, ref: RefType) -> BaseVariable:
        r"""
        Access a variable by its reference.

        :param ref: Reference to the variable to be accessed.
        :return: Variable associated with reference `ref`.
        """
        ...

    @_abc_.abstractmethod
    def __delitem__(self, ref: RefType) -> None:
        r"""
        Delete a variable by its reference.
        Implementation shall remove access to the variable,
        and release any resources associated with the variable, 
        if necessary.

        :param ref: Reference to the variable to be disabled.
        """
        ...


from ..utils.mappers import StructureMapper

class CompositeVariable(BaseVariable):
    r"""
    TODO
    """

    # TODO typehint: CompositeTypes[BaseVariable]
    def __init__(self, vars):
        self._vars = vars

    @property
    def value(self):
        def getter(o):
            return o.value if isinstance(o, BaseVariable) else o
        return StructureMapper(getter)(self._vars)
    
class MutableCompositeVariable(
    CompositeVariable, 
    BaseMutableVariable,
):
    r"""
    TODO
    """

    @CompositeVariable.value.setter
    def value(self, o):
        def setter(o, val):
            if isinstance(o, BaseVariable):
                o.value = val
                return val
            return None
        return StructureMapper(setter)(self._vars, o)


# TODO
def valueof(o: BaseVariable | Any):
    return o.value if isinstance(o, BaseVariable) else o


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


class VariableProxyMeta(type(BaseVariable)):
    def __new__(
        cls, name, bases, namespace, 
        proxy_attrs: Iterable[str] | Mapping[str, str] = [],
        **kwargs,
    ):

        def make_method(attr):
            def method(self, *args, **kwargs):
                class ProxyComputeVariable(
                    ComputedVariable, 
                    metaclass=VariableProxyMeta, 
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


from .. import utils as _utils_


class VariableNumOpsMixin(
    BaseVariable,
    metaclass=VariableProxyMeta,
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
from .refs import RefManager

# TODO just valueof()? Iterator => StreamVariable?
class VariableRefManager(
    RefManager[None | BaseVariable | Iterator],
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
            from ..specs.exceptions import TemporaryUnavailableError
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
    'RefType',
    'VariableRefManager',
]
