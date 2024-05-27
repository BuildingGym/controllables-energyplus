# from __future__ import annotations

import abc as _abc_
import typing as _typing_
import collections as _collections_
import functools as _functools_

from .containers import CallableSet

BaseEventRef = _typing_.Hashable

class BaseEvent(_typing_.Protocol):
    ref: BaseEventRef

BaseEventHandler = _typing_.Callable[[BaseEvent], _typing_.Any]

class BaseEventManager(_abc_.ABC):
    @_functools_.cached_property
    def _handlers(self) -> _typing_.Mapping[BaseEventRef, CallableSet]:
        return _collections_.defaultdict(CallableSet)

    def on(
        self,
        ref: BaseEventRef,
        *handlers: BaseEventHandler,
    ):
        self._handlers[ref].update(handlers)
        return self

    def off(
        self,
        ref: BaseEventRef,
        *handlers: BaseEventHandler,
    ):
        self._handlers[ref].difference_update(handlers)
        return self
    
    def trigger(
        self,
        event: BaseEvent,
        *args, **kwargs,
    ):
        return self._handlers[event.ref](event, *args, **kwargs)


__all__ = [
    'BaseEventRef',
    'BaseEventHandler',
    'BaseEvent',
    'BaseEventManager',
]