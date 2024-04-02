from __future__ import annotations

import abc as _abc_
import typing as _typing_
import collections as _collections_
import functools as _functools_

from .. import utils

BaseEventSpecs = _typing_.Hashable

class BaseEvent(_typing_.Protocol):
    specs: BaseEventSpecs

BaseEventHandler = _typing_.Callable[[BaseEvent], _typing_.Any]

class BaseEventManager(_abc_.ABC):
    @_functools_.cached_property
    def _handlers(self) -> _typing_.Mapping[BaseEventSpecs, utils.containers.CallableSet]:
        return _collections_.defaultdict(utils.containers.CallableSet)

    def on(
        self,
        specs: BaseEventSpecs,
        *handlers: BaseEventHandler,
    ):
        self._handlers[specs].update(handlers)
        return self

    def off(
        self,
        specs: BaseEventSpecs,
        *handlers: BaseEventHandler,
    ):
        self._handlers[specs].difference_update(handlers)
        return self
    
    def trigger(
        self,
        event: BaseEvent,
        *args, **kwargs,
    ):
        return self._handlers[event.specs](event, *args, **kwargs)


__all__ = [
    BaseEventSpecs,
    BaseEventHandler,
    BaseEvent,
    BaseEventManager,
]