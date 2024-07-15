r"""
Callbacks.
"""


import abc as _abc_
import typing as _typing_
import collections as _collections_
import functools as _functools_
import asyncio as _asyncio_

from typing import Any, Mapping, Self, Callable, Generic, TypeAlias

from ..specs.components import BaseComponent
from ..utils.containers import OrderedSet


_CallableT = _typing_.TypeVar(
    '_CallableT', 
    bound=Callable,
)


class ContinueOperation(Exception):
    r"""
    Signal that the current operation be continued.
    """

    pass

class StopOperation(Exception):
    r"""
    Signal that the current operation be stopped.
    """

    pass


class CallablePipeline(
    OrderedSet[_CallableT],
    Callable,
    Generic[_CallableT],
):
    """
    A "multiplexing" callable for executing a sequence of callables.

    Examples:

    TODO
    """

    # TODO check ret Exception?
    def __call__(self, *args, **kwargs) -> Mapping[_CallableT, Any]:
        r"""
        Execute the callback pipeline.
        Arguments are passed to callbacks in the pipeline.

        If a callback raises:
        * :class:`ContinueOperation`: 
            For the current call, the issuing callback is skipped 
            and its result not recorded in the return value.
            This is equivalent to a ``continue`` statement in a loop.
        * :class:`StopOperation`: 
            For the current call, all callbacks after 
            the issuing callback are skipped 
            and the return value contains only the results before
            the issuing callback.
            This is equivalent to a ``break`` statement in a loop.

        :returns: 
            The results of each callback, 
            keyed by the respective callback.
        """

        res = _collections_.OrderedDict()

        for f in self:
            try: 
                res[f] = f(*args, **kwargs)
            except ContinueOperation: continue
            except StopOperation: break

        return res
    
piped = CallablePipeline
r"""
Shortcut for creating a :class:`CallablePipeline`.
"""


# TODO generic should be ArgsT
class BaseCallback(
    _abc_.ABC,
    Generic[_CallableT],
):
    r"""
    Callback base class.
    """

    @_abc_.abstractmethod
    def on(self, *callables: _CallableT) -> Self:
        r"""
        Add the given callables to the callback.
        This may be used as a decorator.

        :param callables: The callables to add.
        :returns: This callback.
        """

        ...

    @_abc_.abstractmethod
    def off(self, *callables: _CallableT) -> Self:
        r"""
        Remove the given callables from the callback.
        This may be used as a decorator.

        :param callables: The callables to remove.
        :returns: This callback.
        """

        ...

    @_abc_.abstractmethod
    def __call__(self, *args, **kwargs) -> Mapping[_CallableT, Any]:
        r"""
        Emit the callback with the given arguments.
        This will execute all enabled callables.

        :returns: 
            The return values of each callable, 
            keyed by their respective callables.
        """

        ...

    @_abc_.abstractmethod
    def fork(
        self, 
        transform: Callable[['BaseCallback'], 'BaseCallback'] | None = None,
    ) -> 'BaseCallback[_CallableT]':
        r"""
        Create a new namespace under this callback.
        This namespace shall:
        * have its own set of callables 
            (accessible via :meth:`on` and :meth:`off`)
        * emit when the parent callback emits 
            (accessible via :meth:`__call__`)

        :param transform:
            A function to transform the created callback instance.
            This can be used to wrap the new callback 
            with additional functionality.
        :returns: 
            A child callback instance attached to this callback.
        """

        ...



_RefT = _typing_.TypeVar(
    '_RefT', 
    bound=_typing_.Hashable,
)

# TODO _CallbackT instead
class BaseCallbackManager(
    _abc_.ABC,
    _typing_.Generic[
        _RefT, 
        _CallableT,
    ],
):
    r"""
    Callback manager base class.
    """
    
    @_abc_.abstractmethod
    def __getitem__(self, ref: _RefT) -> BaseCallback[_CallableT]:
        r"""
        Access the callback for the reference.
        
        :param ref: The reference.
        :returns: The callback.
        """

        ...
    
    @_abc_.abstractmethod
    def on(
        self, 
        ref: _RefT, 
        *callables: _CallableT,
    ) -> Self:
        r"""
        Enable the given callables for the reference.

        :param ref: The reference.
        :param callables: The callables to enable.
        """

        ...
    
    @_abc_.abstractmethod
    def off(
        self, 
        ref: _RefT, 
        *callables: _CallableT,
    ) -> Self:
        r"""
        Disable the given callables for the reference.

        :param ref: The reference.
        :param callables: The callables to disable.
        """

        ...
    
    @_abc_.abstractmethod
    def __call__(
        self,
        ref: _RefT,
        *args, **kwargs,
    ) -> Mapping[_CallableT, Any]:
        r"""
        Emit the reference with the given arguments.
        This will execute all enabled callables for 
        the reference specified.

        :param ref: The reference.
        :returns: 
            The return values of each callable, 
            keyed by their respective callables.
        """

        ...


import itertools as _itertools_
import dataclasses as _dataclasses_
import threading as _threading_


@_dataclasses_.dataclass
class CallbackContext:
    class Input:
        r"""TODO"""

        def __init__(self, *args, **kwargs):
            self.__args__ = args
            self.__kwargs__ = kwargs

        def keys(self):
            return _itertools_.chain(
                range(len(self.__args__)),
                self.__kwargs__.keys(),
            )

        def values(self):
            return _itertools_.chain(
                self.__args__, 
                self.__kwargs__.values(),
            )
        
        def __iter__(self):
            return self.values()
        
        def __getitem__(self, key):
            if key in self.__args__:
                return self.__args__[key]
            return self.__kwargs__[key]

        def __repr__(self):
            args_r = str.join(', ', (repr(arg) for arg in self.__args__))
            kwargs_r = str.join(', ', 
                (f'{k}={v!r}' for k, v in self.__kwargs__.items()))
            return f'{self.__class__.__name__}({args_r}, {kwargs_r})'
        
    class Output:
        def __init__(self, deferred: bool = False):
            self.__result__ = None
            self.__done__ = _threading_.Event() if deferred else None

        def __call__(self, value):
            if self.__done__ is not None:
                self.__done__.set()
            self.__result__ = value
            return self
        
        def get(self, timeout: float | None = None):
            if self.__done__ is not None:
                self.__done__.wait(timeout=timeout)
            return self.__result__
        
    input: Input
    output: Output

    @property
    def args(self):
        return self.input
    
    def ack(self, value=None):
        self.output(value)
        return self.output


class CallbackAsyncOpsMixin(BaseCallback):
    r"""
    Asynchronous operations mixin for callbacks.
    TODO

    .. code-block:: python
        class Callback(BaseCallback, CallbackAsyncOpsMixin):
            ...
        
        callback = Callback()
        # meanwhile, in another thread, probably...
        # callback.emit(...)

        while True:
            # if acknolwedgement is NOT necessary...
            res = await callback        

            # otherwise...
            res = await callback.awaitable(deferred=True)
            # ... do some processing and have the callback thread wait for it
            res.ack('roger!')
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
            -> _asyncio_.Future[CallbackContext]:
            r"""
            Create an awaitable for the callback.

            :returns: A future that resolves when the callback is emitted.
            """

            loop = self._loop or _asyncio_.get_event_loop()
            future = loop.create_future()
            
            def _listener(*args, **kwargs):
                self._manager.off(_listener)
                ctx = CallbackContext(
                    input=CallbackContext.Input(*args, **kwargs),
                    output=CallbackContext.Output(deferred=deferred),
                )
                loop.call_soon_threadsafe(future.set_result, ctx)
                return ctx.output.get()
            self._manager.on(_listener)

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
    

class CallbackProxy(
    BaseCallback,
):
    def __init__(self, target: BaseCallback):
        self._target = target
    
    def on(self, *callables):
        self._target.on(*callables)
        return self
    
    def off(self, *callables):
        self._target.off(*callables)
        return self
    
    def __call__(self, *args, **kwargs):
        return self._target.__call__(*args, **kwargs)

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

# TODO
class FilteredCallback(CallbackProxy):
    def __init__(self, target: BaseCallback, predicate: Predicate):
        super().__init__(target=target)
        self._filter = predicate

    def __call__(self, *args, **kwargs):
        if not self._filter(*args, **kwargs):
            return None
        return self._target(*args, **kwargs)


class CallbackOpsMixin(
    BaseCallback[_CallableT],
    Generic[_CallableT],
):
    def use(self, callable: _CallableT) -> _CallableT:
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


class Callback(
    CallbackAsyncOpsMixin,
    CallbackOpsMixin,
    BaseCallback[_CallableT],
    Generic[_CallableT],
):
    @_functools_.cached_property
    def _callables(self):
        return CallablePipeline[_CallableT]()

    def on(self, *callables):
        self._callables.update(callables)
        return self
    
    def off(self, *callables):
        self._callables.difference_update(callables)
        return self
    
    def __call__(self, *args, **kwargs):
        return self._callables.__call__(*args, **kwargs)
    
    def fork(self, transform=None):
        cb = Callback()
        if transform is not None:
            cb = transform(cb)
        self.on(cb)
        return cb


class CallbackManager(
    dict[_RefT, Callback[_CallableT]],
    BaseCallbackManager[
        _RefT, 
        _CallableT,
    ],
):
    r"""
    A manager for callbacks.
    """

    def __missing__(self, ref: _RefT):
        r"""
        TODO doc
        """

        self[ref] = Callback()
        return self[ref]
    
    def __getitem__(self, ref: _RefT):
        return super().__getitem__(ref)
    
    def __repr__(self):
        return object.__repr__(self)
    
    def on(
        self, 
        ref: _RefT, 
        *callables: _CallableT,
    ):
        self[ref].on(*callables)
        return self
    
    def off(
        self, 
        ref: _RefT, 
        *callables: _CallableT,
    ):
        self[ref].off(*callables)
        return self
    
    def __call__(
        self,
        ref: _RefT,
        *args, **kwargs,
    ):
        return self[ref].__call__(*args, **kwargs)


__all__ = [
    'CallablePipeline',
    'piped',
    'Callback',
    'CallbackManager',
]
