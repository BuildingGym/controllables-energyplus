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
)

from .callables import (
    ArgsT,
    RetT,
    CallablePipeline, 
    ExecutionContext,
)
from .components import BaseComponent
from .refs import BaseRefManager


class BaseCallback(
    _abc_.ABC,
    Generic[ArgsT, RetT],
):
    r"""
    Callback base class.

    A callback is a :class:`set`-like container 
    for :class:`callable`s.
    """

    @_abc_.abstractmethod
    def on(self, func: Callable[ArgsT, RetT]) -> Callable[ArgsT, RetT]:
        r"""
        Add a :class:`callable`.
        This may be used as a decorator.

        :param func: The :class:`callable` to add.
        :returns: The :class:`callable` added.
        """

        ...

    @_abc_.abstractmethod
    def off(self, func: Callable[ArgsT, RetT]) -> Callable[ArgsT, RetT]:
        r"""
        Remove a :class:`callable`.
        This may be used as a decorator.

        :param func: The :class:`callable` to remove.
        :returns: The :class:`callable` removed.
        """

        ...

    @_abc_.abstractmethod
    def __call__(self, *args: ArgsT.args, **kwargs: ArgsT.kwargs) \
        -> Mapping[Callable[ArgsT, RetT], RetT]:
        r"""
        Call this callback with arguments.
        This shall execute all :class:`callable`s 
        added through :meth:`on`.

        :returns: 
            The return values of each :class:`callable`, 
            keyed by their respective :class:`callable`s.
        """

        ...

    @_abc_.abstractmethod
    def fork(
        self, 
        transform: Callable[['BaseCallback'], 'BaseCallback'] | None = None,
    ) -> 'BaseCallback':
        r"""
        Create a new namespace under this callback.
        This namespace shall:
            * have its own set of callables 
                (accessible via :meth:`on` and :meth:`off`)
            * emit when its parent callback emits 
                (accessible via :meth:`__call__`)

        :param transform:
            A function to transform the created callback.
            This can be used to wrap the new callback 
            with additional functionality.
        :returns: 
            A child callback attached to this callback.
        """

        ...


_RefT = TypeVar('_RefT')
_CallbackT = TypeVar(
    '_CallbackT', 
    bound=BaseCallback,
)

class BaseCallbackManager(
    BaseRefManager[_RefT, _CallbackT],
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
        :returns: The callback.
        """

        ...

    @_abc_.abstractmethod
    def __contains__(self, ref: _RefT) -> bool:
        r"""
        Check if the reference exists in this manager.

        :param ref: The reference.
        :returns: Whether the reference exists.
        """

        ...
    
    def on(self, ref: _RefT, func: Callable) -> Callable:
        r"""
        Add a :class:`callable`.

        :param ref: The reference to use for `func`.
        :param func: The :class:`callable` to add.
        :returns: The added :class:`callable`.
        """

        self[ref].on(func)
        return func
    
    def off(self, ref: _RefT, func: Callable) -> Callable:
        r"""
        Remove a :class:`callable`.

        :param ref: The reference.
        :param func: The :class:`callable` to remove.
        :returns: The removed :class:`callable`.
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
        :returns: 
            The return values of each :class:`callable`, 
            keyed by their respective :class:`callable`s.
        """

        return self[ref].__call__(*args, **kwargs)


class CallbackSyncOpsMixin(BaseCallback):
    r"""
    Synchronous operations mixin for callbacks.
    TODO

    """

    class SyncOps(BaseComponent[BaseCallback]):
        def __call__(self, deferred: bool = False) \
            -> _concurrent_futures_.Future[ExecutionContext]:
            future = _concurrent_futures_.Future()
            
            @self._manager.on
            def _listener(*args, **kwargs):
                self._manager.off(_listener)
                ctx = ExecutionContext(
                    vars=ExecutionContext.Arguments(*args, **kwargs),
                    ack=ExecutionContext.Ack(deferred=deferred),
                )
                future.set_result(ctx)
                return ctx.ack.get()

            return future
        
    @_functools_.cached_property
    def waitable(self):
        return self.SyncOps().__attach__(self)
    
    def wait(
        self, 
        deferred: bool = False, 
        timeout: float | None = None,
    ):
        return self.waitable(deferred=deferred).result(timeout=timeout)


class CallbackAsyncOpsMixin(BaseCallback):
    r"""
    Asynchronous operations mixin for callbacks.
    TODO

    .. code-block:: python
        class Callback(BaseCallback, CallbackAsyncOpsMixin):
            ...
        
        callback = Callback()
        # meanwhile, in another thread, probably...
        # callback(...)

        while True:
            # if acknolwedgement is NOT necessary...
            ctx = await callback        

            # otherwise...
            ctx = await callback.awaitable(deferred=True)
            # do some processing and have the callback caller wait for it
            # signal the caller with a return value
            ctx.ack('roger!')
    """
    
    class AsyncOps(BaseComponent[BaseCallback]):
        r"""
        Asynchronous operations.
        """
                        
        def __init__(self, loop: _asyncio_.AbstractEventLoop = None):
            r"""
            Initialize the async operations mixin.

            :param loop: 
                The event loop to use.
                If :class:`None` or unspecified,
                the default event loop is used.
            """

            self._loop = loop

        def __call__(self, deferred: bool = False) \
            -> _asyncio_.Future[ExecutionContext]:
            r"""
            Create an awaitable for the callback.

            :returns: A future that resolves when the callback is emitted.
            """

            loop = self._loop or _asyncio_.get_event_loop()
            future = loop.create_future()
            
            @self._manager.on
            def _listener(*args, **kwargs):
                self._manager.off(_listener)
                ctx = ExecutionContext(
                    vars=ExecutionContext.Arguments(*args, **kwargs),
                    ack=ExecutionContext.Ack(deferred=deferred),
                )
                loop.call_soon_threadsafe(
                    future.set_result, ctx,
                )
                return ctx.ack.get()

            return future
                
    @_functools_.cached_property
    def awaitable(self):
        r"""
        Asynchronous interface.
        """

        return self.AsyncOps().__attach__(self)
    
    def __await__(self):
        r"""
        Await the callback (Shortcut).

        :returns: See base method.

        .. seealso:: :meth:``AsyncOps.__await__``
        """

        return self.awaitable().__await__()
    

class CallbackProxy(BaseCallback):
    def __init__(self, target: BaseCallback):
        self._target = target
    
    def on(self, func):
        return self._target.on(func)
    
    def off(self, func):
        return self._target.off(func)
    
    def __call__(self, *args, **kwargs):
        return self._target.__call__(*args, **kwargs)
    
    def fork(self, transform=None):
        return self._target.fork(transform=transform)


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
    def __init__(self, target: BaseCallback, predicate: Predicate):
        super().__init__(target=target)
        self._predicate = predicate

    def __call__(self, *args, **kwargs):
        if not self._predicate(*args, **kwargs):
            return None
        return super().__call__(*args, **kwargs)


class CallbackOpsMixin(BaseCallback):
    r"""TODO"""

    # TODO !!!!
    def use(self, callable: Callable) -> Callable:
        r"""
        TODO
        """
        
        self.on(callable)
        return callable
    
    def filter(self, predicate: Predicate) -> FilteredCallback:
        return self.fork(
            transform=lambda cb, predicate=predicate: FilteredCallback(
                target=cb, 
                predicate=predicate,
            ),
        )

    class SamplerConstructor:
        def __init__(self, parent: 'CallbackOpsMixin'):
            self._parent = parent

        def uniform(self, interval: int):
            return self._parent.filter(FrequencyPredicate(freq=interval))

        def __call__(self, interval: int):
            return self.uniform(interval=interval)

    @property
    def sample(self):
        return self.SamplerConstructor(parent=self)
    
    def __or__(self, other: BaseCallback) -> 'Callback':
        # TODO

        raise NotImplementedError
    
    def __mod__(self, interval: int) -> 'Callback':
        return self.sample.uniform(interval=interval)


class Callback(
    CallbackOpsMixin,
    CallbackSyncOpsMixin,
    CallbackAsyncOpsMixin,
    BaseCallback[ArgsT, RetT],
    Generic[ArgsT, RetT],
):
    @_functools_.cached_property
    def _callables(self):
        return CallablePipeline()

    def on(self, func):
        self._callables.add(func)
        return func
    
    def off(self, func):
        self._callables.discard(func)
        return func
    
    def __call__(self, *args, **kwargs):
        return self._callables.__call__(*args, **kwargs)
    
    def fork(self, transform=None):
        cb = Callback()
        if transform is not None:
            cb = transform(cb)
        self.on(cb)
        return cb


class CallbackManager(
    #dict[_RefT, _CallbackT],
    BaseCallbackManager[_RefT, _CallbackT],
):
    r"""
    A manager for callbacks.
    """

    @_functools_.cached_property
    def _callbacks(self) -> dict[_RefT, _CallbackT]:
        return dict()
    
    def __contains__(self, ref):
        return ref in self._callbacks

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
