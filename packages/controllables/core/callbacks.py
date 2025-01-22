r"""
Callbacks.
"""


import abc as _abc_
import functools as _functools_
import asyncio as _asyncio_
import concurrent.futures as _concurrent_futures_
from typing import (
    Any, 
    Callable, 
    Generic, 
    Mapping, 
    TypeAlias, 
    TypeVar,
    Iterable,
)

from .callables import (
    ArgsT,
    RetT,
    CallableSequence, 
    CancelledError,
    ExecutionContext,
)
from .components import Component
from .errors import ExceptionableMixin
from .refs import ProtoRefManager


# TODO destructor
class BaseHandler(
    Callable,
    Component['ProtoCallback'],
    _abc_.ABC,
):
    def cancel(self, message: Any) -> None:
        ...


class ProtoCallback(
    _abc_.ABC,
    Generic[ArgsT, RetT],
):
    r"""
    Callback protocol class.

    A callback is a :class:`set`-like container 
    for :class:`callable`s.
    """

    @_abc_.abstractmethod
    def on(self, func: Callable[ArgsT, RetT]) -> Callable[ArgsT, RetT]:
        r"""
        Add a :class:`callable`.
        This may be used as a decorator.

        :param func: The :class:`callable` to add.
        :return: The :class:`callable` added.
        """

        ...

    @_abc_.abstractmethod
    def off(self, func: Callable[ArgsT, RetT]) -> Callable[ArgsT, RetT]:
        r"""
        Remove a :class:`callable`.
        This may be used as a decorator.

        :param func: The :class:`callable` to remove.
        :return: The :class:`callable` removed.
        """

        ...

    @_abc_.abstractmethod
    def __call__(self, *args: ArgsT.args, **kwargs: ArgsT.kwargs) \
        -> Mapping[Callable[ArgsT, RetT], RetT]:
        r"""
        Call this callback with arguments.
        This shall execute all :class:`callable`s 
        added through :meth:`on`.

        :return: 
            The return values of each :class:`callable`, 
            keyed by their respective :class:`callable`s.
        """

        ...

    @_abc_.abstractmethod
    def fork(
        self, 
        transform: Callable[['ProtoCallback'], 'ProtoCallback'] | None = None,
    ) -> 'ProtoCallback':
        r"""
        Create a new namespace under this callback.

        This namespace shall:

        * have its own set of callables (accessible via :meth:`on` and :meth:`off`)
        * emit when its parent callback emits (accessible via :meth:`__call__`)

        :param transform:
            A function to transform the created callback.
            This can be used to wrap the new callback 
            with additional functionality.
        :return: 
            A child callback attached to this callback.
        """

        ...


class CallbackProxy(ProtoCallback):
    def __init__(self, callback: ProtoCallback):
        self.__callback__ = callback
    
    def on(self, func):
        return self.__callback__.on(func)
    
    def off(self, func):
        return self.__callback__.off(func)
    
    def __call__(self, *args, **kwargs):
        return self.__callback__.__call__(*args, **kwargs)
    
    def fork(self, transform=None):
        return self.__callback__.fork(transform=transform)


# TODO
class BaseFutureHandler(
    ExceptionableMixin,
    BaseHandler,
    Component[ProtoCallback],
    _abc_.ABC,
):
    deferred: bool

    @_abc_.abstractmethod
    def _resolve(self, ctx: ExecutionContext): 
        ...

    @_abc_.abstractmethod
    def _cancel(self): 
        ...

    def __call__(self, *args, **kwargs):
        self.parent.off(self)
        self.throw()
        ctx = ExecutionContext(
            vars=ExecutionContext.Arguments(*args, **kwargs),
            ack=ExecutionContext.Ack(deferred=self.deferred),
        )
        self._resolve(ctx)
        res = ctx.ack.get()
        return res

    def cancel(self, message):
        self.err(CancelledError(message))
        self._cancel()



# TODO
class ConcurrentFutureHandler(BaseFutureHandler):
    def __init__(self, deferred: bool = False):
        self.deferred = deferred

    @_functools_.cached_property
    def future(self):
        return _concurrent_futures_.Future()
    
    def _resolve(self, ctx):
        if self.future.cancelled():
            return
        self.future.set_result(ctx)

    def _cancel(self):
        self.future.cancel()


# TODO 
class AsyncFutureHandler(BaseFutureHandler):
    def __init__(
        self, 
        loop: _asyncio_.AbstractEventLoop,
        deferred: bool = False,
    ):
        self.loop = loop
        self.deferred = deferred

    @_functools_.cached_property
    def future(self):
        return self.loop.create_future()

    def _resolve(self, ctx):
        def set_result(future, ctx):
            if future.cancelled():
                return
            future.set_result(ctx)
        self.future.get_loop().call_soon_threadsafe(
            set_result, self.future, ctx,
        )

    def _cancel(self):
        self.future.get_loop().call_soon_threadsafe(
            self.future.cancel,
        )


class CallbackFutureOpsMixin(ProtoCallback):
    def future(self, deferred: bool = False):
        handler = ConcurrentFutureHandler(deferred=deferred)
        self.on(handler)
        return handler.future

    def wait(
        self, 
        deferred: bool = False, 
        timeout: float | None = None,
    ):
        return self.future(deferred=deferred).result(timeout=timeout)

    # TODO
    def queue(
        self,
        begin: 'CallbackFutureOpsMixin | None' = None,
        end: 'CallbackFutureOpsMixin | None' = None,
        deferred: bool = False,
        timeout: float | None = None,
    ):
        r"""
        TODO begin end; stream of futures
        "Plural" form of :meth:`wait`.
        """

        if begin is not None:
            begin.wait()

        while True:
            future = self.future(deferred=deferred)
            if end is not None:
                def cancel(*args, **kwargs): 
                    end.off(cancel)
                    future.cancel()
                end.on(cancel)
            try: yield future.result(timeout=timeout)
            except _concurrent_futures_.CancelledError: break

    def async_future(
        self, 
        deferred: bool = False,
        loop: _asyncio_.AbstractEventLoop | None = None,
    ):
        handler = AsyncFutureHandler(
            loop=loop or _asyncio_.get_event_loop(),
            deferred=deferred,
        )
        self.on(handler)
        return handler.future

    def __await__(self):
        return self.async_future().__await__()

    # TODO
    def async_queue(self):
        raise NotImplementedError
    
    # TODO
    @_functools_.cached_property
    def waitable(self):
        raise DeprecationWarning('use `.future()` instead!!')

    # TODO
    @_functools_.cached_property
    def awaitable(self):
        raise DeprecationWarning('use `.async_future()` instead!!')
    

# TODO mv
Predicate: TypeAlias = Callable[..., bool]

class FrequencyPredicate(Predicate):
    def __init__(self, freq: int | None = None):
        self._freq = freq
        self._counter = 0

    def __call__(self, *args, **kwargs):
        self._counter += 1
        if self._freq is None or self._counter % self._freq == 0:
            self._counter = 0
            return True
        return False


# TODO passthru mixins???
class FilteredCallback(CallbackProxy):
    def __init__(self, callback: ProtoCallback, predicate: Predicate):
        super().__init__(callback=callback)
        self._predicate = predicate

    def __call__(self, *args, **kwargs):
        if not self._predicate(*args, **kwargs):
            return None
        return super().__call__(*args, **kwargs)


class CallbackUtilOpsMixin(ProtoCallback):
    r"""
    Callback utility operations mixin.
    """

    # TODO necesito?
    def observe(self, subject: ProtoCallback):
        subject.on
        raise NotImplementedError

    def filter(self, predicate: Predicate) -> FilteredCallback:
        r"""TODO doc"""

        def transform(cb: BaseCallback):
            return FilteredCallback(callback=cb, predicate=predicate)

        return self.fork(transform=transform)

    class SamplerConstructor:
        def __init__(self, parent: 'CallbackUtilOpsMixin'):
            self._parent = parent

        def uniform(self, interval: int):
            return self._parent.filter(FrequencyPredicate(freq=interval))

        def __call__(self, interval: int):
            return self.uniform(interval=interval)

    @property
    def sample(self):
        return self.SamplerConstructor(parent=self)
    
    def __or__(self, other: ProtoCallback):
        # TODO
        raise NotImplementedError
    
    # TODO necesito?
    def __mod__(self, interval: int):
        return self.sample.uniform(interval=interval)


class BaseCallback(
    CallbackFutureOpsMixin,
    CallbackUtilOpsMixin,
    ProtoCallback[ArgsT, RetT],
    _abc_.ABC,
    Generic[ArgsT, RetT],
):
    pass


_RefT = TypeVar('_RefT')
_CallbackT = TypeVar(
    '_CallbackT', 
    bound=ProtoCallback,
)

class BaseCallbackManager(
    ProtoRefManager[_RefT, _CallbackT],
    _abc_.ABC,
    Generic[_RefT, _CallbackT],
):
    r"""
    Callback manager base class.

    A callback manager is a :class:`dict`-like container for 
    :class:`BaseCallback` instances keyed by references.
    """
    
    @_abc_.abstractmethod
    def __getitem__(self, ref: _RefT) -> _CallbackT:
        r"""
        Access the callback.
        
        :param ref: The reference.
        :return: The callback.
        """

        ...

    @_abc_.abstractmethod
    def __contains__(self, ref: _RefT) -> bool:
        r"""
        Check if the reference exists in this manager.

        :param ref: The reference.
        :return: Whether the reference exists.
        """

        ...
    
    def on(self, ref: _RefT, func: Callable) -> Callable:
        r"""
        Add a :class:`callable`.

        :param ref: The reference to use for `func`.
        :param func: The :class:`callable` to add.
        :return: The added :class:`callable`.
        """

        self[ref].on(func)
        return func
    
    def off(self, ref: _RefT, func: Callable) -> Callable:
        r"""
        Remove a :class:`callable`.

        :param ref: The reference.
        :param func: The :class:`callable` to remove.
        :return: The removed :class:`callable`.
        """

        self[ref].off(func)
        return func
    
    def __call__(
        self,
        ref: _RefT,
        *args, **kwargs,
    ) -> Mapping[Callable, Any]:
        r"""
        Call the reference with the given arguments.
        This will execute all enabled :class:`callable`s for 
        the reference specified.

        :param ref: The reference.
        :return: 
            The return values of each :class:`callable`, 
            keyed by their respective :class:`callable`s.
        """

        return self[ref].__call__(*args, **kwargs)


# TODO attach detach
class Callback(
    BaseCallback[ArgsT, RetT],
    # BaseHandler[ArgsT, RetT],
    Generic[ArgsT, RetT],
):
    r"""
    Callback.

    .. doctest::

        >>> cb = Callback()
        >>> cb.on(lambda x: f'i am {x}') # doctest: +ELLIPSIS
        <function ...>
        >>> cb('a string') # doctest: +ELLIPSIS
        OrderedDict([(<function ...>, 'i am a string')])

    """
    
    @_functools_.cached_property
    def _callables(self):
        return CallableSequence()

    def on(self, func):
        if func in self._callables:
            return func
        if isinstance(func, BaseHandler):
            func.__attach__(self)
        self._callables.add(func)
        return func
    
    def off(self, func):
        if func not in self._callables:
            return func
        self._callables.discard(func)
        if isinstance(func, BaseHandler):
            func.__detach__(self)
        return func

    # TODO
    def cancel(self, message):
        for func in self._callables:
            if isinstance(func, BaseHandler):
                func.cancel(message)

    # TODO std?
    def clear(self):
        for func in self._callables:
            self.off(func)
    
    def __call__(self, *args, **kwargs):
        return self._callables.__call__(*args, **kwargs)
    
    # TODO __detach__!!!!
    def fork(self, transform=None):
        cb = Callback()
        if transform is not None:
            cb = transform(cb)
        self.on(cb)
        return cb


class CallbackManager(
    #dict[_RefT, _CallbackT],
    BaseCallbackManager[_RefT, _CallbackT],
    Generic[_RefT, _CallbackT],
):
    r"""
    A manager for callbacks.

    .. doctest::

        >>> callbacks = CallbackManager(slots=['holler'])
        >>> 'holler' in callbacks
        True
        >>> callbacks['holler'].on(lambda x: x) # doctest: +ELLIPSIS
        <function ...>
        >>> callbacks['holler'].on(lambda x: f'{x}!') # doctest: +ELLIPSIS
        <function ...>
        >>> callbacks['holler']('just do it') # doctest: +ELLIPSIS
        OrderedDict([(<function ...>, 'just do it'), (<function ...>, 'just do it!')])

    """

    def __init__(
        self, 
        callbacks: Mapping[_RefT, _CallbackT] | None = None,
        slots: Iterable[_RefT] = [],
    ):
        self._slots = set(slots)
        self._callbacks: dict[_RefT, _CallbackT | Callback] = (
            callbacks if callbacks is not None else dict()
        )
    
    def __contains__(self, ref):
        return ref in self._slots or ref in self._callbacks

    # TODO mv to __getitem__ and DO NOT RELY ON DICT!!!!
    def __missing__(self, ref):
        r"""
        TODO doc
        """

        self._callbacks[ref] = Callback()
        return self._callbacks[ref]
    
    def __getitem__(self, ref):
        if ref not in self._callbacks:
            return self.__missing__(ref)
        return self._callbacks[ref]
    
    # def __repr__(self):
    #     return object.__repr__(self)
    
    def __call__(self, ref, *args, **kwargs):
        return self[ref].__call__(*args, **kwargs)


__all__ = [
    'BaseCallback',
    'BaseCallbackManager',
    'Callback',
    'CallbackManager',
]
