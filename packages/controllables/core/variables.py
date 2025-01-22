r"""
Variables.

* Mutation

.. doctest::
    >>> var = MutableVariable('a string')
    >>> var.value
    'a string'
    >>> var.value = 'another string'
    >>> var.value
    'another string'

* Composition

TODO
.. doctest::
    >>> composite_var = CompositeVariable([
    ...     Variable('i am'),
    ...     Variable('a string'),
    ... ])
    >>> composite_var.value
    ['i am', 'a string']

* Evaluation

TODO

"""


import abc as _abc_
import functools as _functools_
import operator as _operator_
from typing import (
    Any, 
    Callable, 
    Generic, 
    Iterable, 
    Literal,
    Mapping,
    ParamSpec,
    Protocol,
    TypeAlias,
    TypeVar,
)

from .callbacks import (
    BaseCallback, 
    BaseCallbackManager,
    Callback,
    CallbackManager,
)
from .components import Component
from .errors import TemporaryUnavailableError
from .refs import RefT, ProtoRefManager
from .utils.mappers import BaseMapper, CollectionMapper


ValT = TypeVar('ValT')


class NilType(type):
    r"""
    :class:`NoneType`-like metaclass for representing nil values.
    """

    def __bool__(self):
        return False
    

class Nil(metaclass=NilType):
    r"""
    :class:`None`-like class for representing nil values.

    .. doctest::

        >>> if not Nil: 
        ...     print(f"that's so {bool(Nil)}!")
        that's so False!
        >>> Nil is None
        False
        >>> Nil is False
        False

    """
    
    pass


class ProtoVariable(
    _abc_.ABC,
    Generic[ValT],
):
    r"""
    Variable protocol class.
    """

    events: CallbackManager[
        Literal['change'],
        Callback,
    ] | None = None
    r"""
    Events associated with this variable.
    """

    @property
    @_abc_.abstractmethod
    def value(self) -> ValT | Nil:
        r"""
        The value of this variable.
        """

        ...


VarT = TypeVar('VarT', bound=ProtoVariable)


# TODO valueof()? Iterator => StreamVariable?
def valueof(obj: ProtoVariable | Any):
    r"""
    Get the value of a variable or object.

    :param obj: The object to get the value of.
    :return: The value of the object.
    """

    return obj.value if isinstance(obj, ProtoVariable) else obj


class ProtoMutableVariable(
    ProtoVariable[ValT],
    _abc_.ABC,
    Generic[ValT],
):
    r"""
    Mutable variable protocol class.
    """

    @ProtoVariable.value.setter
    @_abc_.abstractmethod
    def value(self, val: ValT | Nil):
        r"""
        Set the value of this variable.

        :param val: The value to set.
        """

        ...


class VariableArithOpsMixin(ProtoVariable):
    def __lt__(self, other):
        return compute(_operator_.lt, self, other)
    
    def __le__(self, other):
        return compute(_operator_.le, self, other)
    
    def __eq__(self, other):
        return compute(_operator_.eq, self, other)
    
    def __ne__(self, other):
        return compute(_operator_.ne, self, other)
    
    def __gt__(self, other):
        return compute(_operator_.gt, self, other)
    
    def __ge__(self, other):
        return compute(_operator_.ge, self, other)

    def __add__(self, other):
        return compute(_operator_.add, self, other)

    def __sub__(self, other):
        return compute(_operator_.sub, self, other)

    def __mul__(self, other):
        return compute(_operator_.mul, self, other)
    
    def __matmul__(self, other):
        return compute(_operator_.matmul, self, other)
    
    def __truediv__(self, other):
        return compute(_operator_.truediv, self, other)

    def __floordiv__(self, other):
        return compute(_operator_.floordiv, self, other)
    
    def __mod__(self, other):
        return compute(_operator_.mod, self, other)
    
    def __pow__(self, other):
        return compute(_operator_.pow, self, other)
    
    def __lshift__(self, other):
        return compute(_operator_.lshift, self, other)
    
    def __rshift__(self, other):
        return compute(_operator_.rshift, self, other)
    
    def __and__(self, other):
        return compute(_operator_.and_, self, other)

    def __xor__(self, other):
        return compute(_operator_.xor, self, other)
    
    def __or__(self, other):
        return compute(_operator_.or_, self, other)
    
    def __neg__(self):
        return compute(_operator_.neg, self)
    
    def __pos__(self):
        return compute(_operator_.pos, self)
    
    def __abs__(self):
        return compute(_operator_.abs, self)
    
    def __invert__(self):
        return compute(_operator_.invert, self)


class VariableContainerOpsMixin(ProtoVariable):
    def __getitem__(self, key):
        return IndexVariable(self, key)


class VariableUtilOpsMixin(ProtoVariable):
    def const(self):
        r"""
        Create a constant (aka. readonly, immutable) view of this variable.

        :return: The constant view.
        """

        return VariableView(self)
    
    def cast(self, transform: Callable[[ValT], ValT], **transform_kwds):
        r"""
        Create a readonly transformed copy of this variable.

        :param transform: The transformation function.
        :return: The readonly transformed copy.
        """

        return ComputedVariable.from_operator(transform, self, **transform_kwds)

    def when(self, predicate_or_match: Callable[[ValT], bool] | Any = True):
        r"""
        Create a conditional callback that is triggered when
        the given predicate evaluates to :obj:`True` at 
        subscription time or in the future, when the value 
        of the variable changes.

        TODO doctest

        :param predicate_or_match: The predicate or value to match.
        :return: The conditional callback.
        """

        predicate = predicate_or_match
        if not isinstance(predicate, Callable):
            def predicate(val):
                return val == predicate_or_match

        conditional = Conditional(predicate=predicate)
        conditional.__attach__(self)
        return conditional


class BaseVariable(
    VariableArithOpsMixin,
    VariableContainerOpsMixin,
    VariableUtilOpsMixin,
    ProtoVariable[ValT],
    _abc_.ABC,
    Generic[ValT],
):
    r"""
    Variable base class.
    """

    pass


class BaseMutableVariable(
    BaseVariable[ValT],
    ProtoMutableVariable[ValT],
    _abc_.ABC,
    Generic[ValT],
):
    r"""
    Mutable variable base class.
    """

    pass


# TODO generics? 
class BaseVariableManager(
    ProtoRefManager[RefT, VarT],
    _abc_.ABC,
    Generic[RefT, VarT],
):
    r"""
    Variable manager base class.
    """

    @_abc_.abstractmethod
    def __delitem__(self, ref: RefT) -> None:
        r"""
        Delete a variable by its reference.
        Implementation shall remove access to the variable,
        and release any resources associated with the variable, 
        if necessary.

        :param ref: Reference to the variable to be deleted.
        """

        ...


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
    @_abc_.abstractmethod
    def __mapper__(self, next_mapper: 'BaseMapper') -> 'BaseMapper':
        r"""
        The mapper for the composite variable.

        Typically, this should define how elements 
        of the composite variable need to be _discovered_
        (e.g. elements in a :class:`list`, values in a :class:`dict`);
        Implementation should then _apply_ ``next_mapper`` to the 
        discovered elements.

        :param next_mapper: 
            The base mapper to be applied to 
            the individual elements of :attr:`__variables__`.
        :return: The mapper to be applied to :attr:`__variables__`.
        """
        
        ...

    __variables__: Any
    r"""
    The variables contained in this composite variable.
    Permissible types determined by :attr:`__mapper__`.

    .. note:: This MUST be overridden in subclasses.
    """

    @_functools_.cached_property
    def events(self):
        # TODO
        callbacks = CallbackManager()

        @self.__mapper__
        def setup(variable):
            if not isinstance(variable, ProtoVariable):
                return
            if variable.events is not None:
                if 'change' in variable.events:
                    variable.events['change'].on(callbacks['change'])
        setup(self.__variables__)

        return callbacks

    @property
    def value(self):
        @self.__mapper__
        def getter(variable):
            return valueof(variable)
        return getter(self.__variables__)


class BaseMutableCompositeVariable(
    BaseCompositeVariable, 
    BaseMutableVariable,
    _abc_.ABC,
):
    r"""
    Mutable composite variable base class.

    .. note::
        ALL elements of the composite variable MUST 
        be :class:`ProtoVariable` instances and mutable.
    """

    @property
    def value(self):
        return super().value

    @value.setter
    def value(self, o):
        @self.__mapper__
        def setter(var, val):
            if not isinstance(var, ProtoVariable):
                raise TypeError(f'Expected {ProtoVariable}, got {var!r}')
            var.value = val
            return val
        return setter(self.__variables__, o)


# TODO BaseVariable!!!!
# TODO events
# TODO metaclass=VariableProxyMeta
class ComputedVariable(
    BaseVariable[ValT],
    Generic[
        _ParamT := ParamSpec(
            '_ParamT', 
            bound=ProtoVariable | Any,
        ), 
        ValT,
    ],
):
    r"""
    Computed variable.
    This is a variable whose value is computed from other variables.

    TODO update when any of `BaseVariable` passed is updated!!!!

    .. doctest::
        
        >>> computed_var = ComputedVariable(
        ...     lambda a, b: a.value + ' ' + b,
        ...     a=Variable('i am'), b='a string',
        ... )
        >>> computed_var.value
        'i am a string'

    """

    @classmethod
    def from_operator(
        cls, 
        operator: Callable[_ParamT, ValT], 
        *args: _ParamT.args, 
        **kwargs: _ParamT.kwargs,
    ):
        def operator_(*args, **kwargs):
            return operator(
                *(valueof(o) for o in args), 
                **{k: valueof(v) for k, v in kwargs.items()},
            )
        
        return cls(operator_, *args, **kwargs)

    def __init__(
        self, 
        func: Callable[_ParamT, ValT], 
        *args: _ParamT.args, 
        **kwargs: _ParamT.kwargs,
    ):
        self.__func__ = func
        self.__args__ = args
        self.__kwargs__ = kwargs

    @property
    def __variables__(self) -> Iterable[ProtoVariable]:
        return filter(
            lambda o: isinstance(o, ProtoVariable), 
            (*self.__args__, *self.__kwargs__.values()),
        )

    @_functools_.cached_property
    def events(self):
        callbacks = CallbackManager()
        for var in self.__variables__:
            if var.events is not None:
                if 'change' in var.events:
                    var.events['change'].on(callbacks['change'])
        return callbacks

    @property
    def value(self):
        return self.__func__(*self.__args__, **self.__kwargs__)


compute = ComputedVariable.from_operator
r"""
TODO

.. doctest::

    >>> compute(lambda a, b: f'{a} {b}', 'i am', var('a string'))
    'i am a string'

"""


class IndexVariable(BaseMutableVariable):
    r"""
    Index variable.

    TODO
    """

    def __init__(self, target: ProtoVariable | Any, key: ProtoVariable | Any):
        self.__target__ = target
        self.__key__ = key

    @_functools_.cached_property
    def events(self):
        callbacks = CallbackManager()
        for var in (self.__target__, self.__key__):
            if var.events is not None:
                if 'change' in var.events:
                    var.events['change'].on(callbacks['change'])
        return callbacks

    @property
    def value(self):
        return (
            valueof(self.__target__)
            .__getitem__(valueof(self.__key__))
        )

    @value.setter
    def value(self, val):
        return (
            valueof(self.__target__)
            .__setitem__(valueof(self.__key__), val)
        )


class Conditional(
    Component[ProtoVariable[ValT]],
    Callback[[], Any],
):
    r"""
    Conditional callback.

    .. doctest::

        >>> var = MutableVariable(True)
        >>> conditional = Conditional(lambda val: val)
        >>> conditional.__attach__(var)
        >>> _ = conditional.on(lambda: print(rf"that's so {var.value}!"))
        that's so True!
        >>> var.value = False
        >>> var.value = True
        that's so True!

    """

    def __init__(self, predicate: Callable[[ValT], bool]):
        super().__init__()
        self.__predicate__ = predicate

    def __attach__(self, parent):
        super().__attach__(parent)
        if self.parent.events is not None:
            if 'change' in self.parent.events:
                self.parent.events['change'].on(self)

    def __detach__(self):
        if self.parent.events is not None:
            if 'change' in self.parent.events:
                self.parent.events['change'].off(self)
        super().__detach__()
    
    def on(self, func):
        res = super().on(func)
        self.__call__(__target__=func)
        return res

    def __call__(self, *args, __target__=None, **kwargs):
        try: val = self.parent.value
        except TemporaryUnavailableError: 
            return
        if self.__predicate__(val):
            if __target__ is not None:
                return __target__()
            return super().__call__()


class VariableView(BaseCompositeVariable):
    def __init__(self, variable: ProtoVariable):
        self.__variables__ = variable

    def __mapper__(self, next_mapper):
        return next_mapper


class Variable(
    Generic[ValT],
    BaseVariable[ValT], 
    _abc_.ABC,
):
    r"""
    Variable.

    .. doctest::

        >>> var = Variable('a string')
        >>> var.value
        'a string'

    """

    def __init__(self, value: ValT = Nil):
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
    Generic[ValT],
    Variable[ValT],
    _abc_.ABC,
):
    r"""
    Mutable variable.
    
    .. doctest::

        >>> var = MutableVariable('a string')
        >>> var.value
        'a string'
        >>> var.value = 'another string'
        >>> var.value
        'another string'

        >>> var.events['change'].on(lambda: print('changed')) # doctest: +ELLIPSIS
        <function ...>
        >>> var.value = 'yet another string'
        changed

    """

    @_functools_.cached_property
    def events(self):
        return CallbackManager(slots=['change'])

    @property
    def value(self):
        return super().value    

    @value.setter
    def value(self, o: ValT):
        self.__value__ = o
        # TODO !!!!!
        self.events['change']()


# TODO as variable?
class VariableManager(
    BaseVariableManager[RefT, VarT],
    _abc_.ABC,
    Generic[RefT, VarT],
):
    def __init__(
        self, 
        variables: Mapping[RefT, VarT] | None = None, 
        slots: Iterable[RefT] = [],
    ):
        self._slots = set(slots)
        self._variables: dict[RefT, VarT | MutableVariable] = (
            variables if variables is not None else dict()
        )

    def __contains__(self, ref: RefT):
        return ref in self._slots or ref in self._variables
    
    def __getitem__(self, ref: RefT):
        if ref not in self._variables:
            self._variables[ref] = MutableVariable()
        return self._variables[ref]
    
    def __delitem__(self, ref: RefT):
        del self._variables[ref]


# TODO
def var(obj: ProtoVariable | Any = Nil, copy: bool = False):
    r"""
    TODO

    .. doctest::

        >>> s = var('a string')
        >>> s.value
        'a string'

    """

    if isinstance(obj, ProtoVariable):
        return obj if not copy else MutableVariable(obj.value)
    return MutableVariable(obj)


def const_var(obj: ProtoVariable | Any = Nil, copy: bool = False):
    r"""
    TODO

    .. doctest::

        >>> s = const_var('a string')
        >>> s.value
        'a string'
        >>> const_var(s).value
        'a string'

    """

    if isinstance(obj, ProtoVariable):
        return VariableView(obj) if not copy else Variable(obj.value)
    return Variable(obj)


# TODO typing
class CompositeVariable(
    BaseCompositeVariable,
    _abc_.ABC,
):
    r"""
    Composite variable.

    TODO doc types

    .. doctest::

        >>> composite_var = CompositeVariable([
        ...     Variable('i am'),
        ...     Variable('a string'),
        ... ])
        >>> composite_var.value
        ['i am', 'a string']

        >>> composite_var = CompositeVariable({
        ...     'a': Variable('i am'), 
        ...     'b': [Variable('a string')],
        ... })
        >>> sorted(composite_var.value.items())
        [('a', 'i am'), ('b', ['a string'])]
    
    """

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
    Mutable composite variable.

    .. doctest::

        >>> composite_var = MutableCompositeVariable([
        ...     var0 := MutableVariable('i am'),
        ...     var1 := MutableVariable('a string'),
        ... ])
        >>> composite_var.value = ['this is', 'another string']
        >>> composite_var.value
        ['this is', 'another string']
        >>> var0.value, var1.value
        ('this is', 'another string')

    """

    pass


# TODO typing
def compose(variables: ProtoVariable | Any):
    r"""
    Compose variables into a composite variable.

    :param variables: Variables to be composed.
    :return: The composite variable.
    """

    return CompositeVariable(variables)


def const_compose(variables: ProtoVariable | Any):
    r"""
    Compose constant variables into a composite variable.

    :param variables: Variables to be composed.
    :return: The composite variable.
    """

    return CompositeVariable(variables)


class ProxyMeta(type(BaseVariable)):
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
                    metaclass=ProxyMeta, 
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


__all__ = [
    'ProtoVariable',
    'ProtoMutableVariable',
    'BaseVariable',
    'BaseMutableVariable',
    'BaseVariableManager',
    'Variable',
    'MutableVariable',
    'Conditional',
    'VariableManager',
]
