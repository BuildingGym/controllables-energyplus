
import abc as _abc_
import typing as _typing_
import collections as _collections_
import functools as _functools_

from .containers import OrderedSetDict, CallableSet, OrderedSet

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


import dataclasses as _dataclasses_


TargetT = _typing_.TypeVar('TargetT')

class Event(_typing_.Generic[TargetT]):
    class Ref(_typing_.Hashable, _typing_.Protocol):
        pass

    ref: Ref
    target: TargetT

    def __init__(self, ref: Ref, target: TargetT):
        super().__init__()
        self.ref = ref
        self.target = target

EventCallback = _typing_.Callable[[Event], _typing_.Any]

@_dataclasses_.dataclass(frozen=True)
class EventListener:
    callback: 'EventCallback'
    recurring: bool = True

class EventManager:
    @_functools_.cached_property
    def _listeners(self) -> _typing_.Mapping[Event.Ref, OrderedSet[EventListener]]:
        return _collections_.defaultdict(OrderedSet)
    
    def on(self, ref: Event.Ref, listener: EventListener | EventCallback):
        self._listeners[ref].add(listener)
        return self
    
    def off(self, ref: Event.Ref, listener: EventListener | EventCallback):
        self._listeners[ref].remove(listener)
        return self
    
    def call(
        self,
        ref: Event.Ref, 
        listener: EventListener | EventCallback,
        *args, **kwargs,
    ):
        if isinstance(listener, EventListener):
            res = listener.callback(*args, **kwargs)
            if not listener.recurring:
                self.off(ref, listener)
            return res
        return listener(*args, **kwargs)

    def emit(
        self, 
        ref: Event.Ref, 
        event: Event,
        *args, **kwargs,
    ):
        return {
            ref: self.call(ref, listener, event, *args, **kwargs)
            for listener in self._listeners[ref]
        }


__all__ = [
    'Event',
    'EventManager',
]