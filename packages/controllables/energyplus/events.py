r"""
Events.

.. seealso:: :mod:`controllables.core.callbacks`
"""


import functools as _functools_
import dataclasses as _dataclasses_
from typing import Any, Callable, NamedTuple, TypeAlias

from controllables.core.callbacks import (
    Callback,
    CallbackManager,
    BaseComponent,
)

from .systems import System


@_dataclasses_.dataclass
class Context:
    event: 'Event | None' = None

    @classmethod
    def copyof(cls, obj: 'Event', **changes):
        return _dataclasses_.replace(obj, **changes)

@_dataclasses_.dataclass
class MessageContext(Context):
    r"""
    Context for user message events.

    :param message: The message.
    """

    message: 'str | None' = None

@_dataclasses_.dataclass
class ProgressContext(Context):
    r"""
    Context for progress events.

    :param progress: The progress of the event as a percentage between 0 and 1.
    """

    progress: 'float | None' = None
    

class Event(
    Callback[[Context], Any],
    BaseComponent['EventManager'],
):
    r"""
    A generic event.
    """

    class Ref(NamedTuple):
        r"""
        A reference to an event.
        """

        @classmethod
        def copyof(cls, obj, **changes):
            if isinstance(obj, cls):
                return cls._replace(obj, **changes)            
            if isinstance(obj, str):
                return cls(name=obj, **changes)
            raise TypeError(obj)

        name: str
        r"""The name of the event."""
        include_warmup: bool = False
        r"""
        Whether to include the warmup period.
        
        .. seealso:: 
            https://bigladdersoftware.com/epx/docs/24-1/engineering-reference/warmup-convergence.html#warmup-convergence
        """

    RefT = Ref | str
    r"""The type of the reference to an event."""

    ref: Ref | None
    r"""The reference to an event."""

    def __init__(self, ref: Ref | None = None):
        super().__init__()
        self.ref = ref

    def __call__(self, context: Context):
        if self.ref is not None:
            if not self.ref.include_warmup:
                if self._manager is None:
                    raise RuntimeError(
                        f'"include_warmup" specified in {self.ref} '
                        f'without an {EventManager} {self.__attach__}-ed'
                    )
                if self._manager._core.api \
                    .exchange.warmup_flag(self._manager._core.state):
                    return None

        return super().__call__(context)


class EventManager(
    CallbackManager[Event.RefT, Event],
    BaseComponent[System],
):
    r"""
    Event manager.

    TODOs:
        * TODO child subeventmanager
    """

    @property
    def _core(self):
        return self._manager._kernel

    _CallbackSetters: TypeAlias = dict[str, Callable[[Event], None]]
    
    # TODO assoc defaultdict!!!!!!!
    @_functools_.cached_property
    def _core_callback_setters(self) -> _CallbackSetters:
        r"""
        Callback setters for the core.
        """

        def _ensure_exc(cb: Callable):
            @_functools_.wraps(cb)
            def cb_(*args, **kwargs):
                try:
                    return cb(*args, **kwargs)
                except Exception as e:
                    @self._core.hooks['run:post'].on
                    def _raise_exc(*args, __exc__=e, **kwargs):
                        self._core.hooks['run:post'].off(_raise_exc)
                        raise Exception from __exc__
                    self._core.stop()
            return cb_

        class _Dispatcher:
            def __init__(self, event: Event):
                self._event = event

            def _message(self, m):
                self._event.__call__(
                    MessageContext(
                        event=self._event,
                        message=bytes.decode(m),
                    ),
                )

            def _progress(self, p):
                self._event.__call__(
                    ProgressContext(
                        event=self._event,
                        progress=p / 100,
                    ),
                )

            def _state(self, _):
                self._event.__call__(
                    Context(
                        event=self._event,
                    ),
                )

        runtime = self._core.api.runtime
        state = self._core.state

        return {
            # message
            'message': lambda event: 
                runtime.callback_message(
                    state, 
                    _ensure_exc(_Dispatcher(event)._message),
                ),
            # progress
            'progress': lambda event: 
                runtime.callback_progress(
                    state, 
                    _ensure_exc(_Dispatcher(event)._progress),
                ),
            # state
            **{
                ref: lambda event, callback_setter=callback_setter: 
                    callback_setter(
                        state, 
                        _ensure_exc(_Dispatcher(event)._state),
                    )
                for ref, callback_setter in {
                    'after_component_get_input': runtime.callback_after_component_get_input,
                    'after_new_environment_warmup_complete': runtime.callback_after_new_environment_warmup_complete,
                    'after_predictor_after_hvac_managers': runtime.callback_after_predictor_after_hvac_managers,
                    'after_predictor_before_hvac_managers': runtime.callback_after_predictor_before_hvac_managers,
                    'begin_new_environment': runtime.callback_begin_new_environment,
                    'begin_system_timestep_before_predictor': runtime.callback_begin_system_timestep_before_predictor,
                    'begin_zone_timestep_after_init_heat_balance': runtime.callback_begin_zone_timestep_after_init_heat_balance,
                    'begin_zone_timestep_before_init_heat_balance': runtime.callback_begin_zone_timestep_before_init_heat_balance,
                    'begin_zone_timestep_before_set_current_weather': runtime.callback_begin_zone_timestep_before_set_current_weather,
                    'end_system_sizing': runtime.callback_end_system_sizing,
                    'end_system_timestep_after_hvac_reporting': runtime.callback_end_system_timestep_after_hvac_reporting,
                    'end_system_timestep_before_hvac_reporting': runtime.callback_end_system_timestep_before_hvac_reporting,
                    'end_zone_sizing': runtime.callback_end_zone_sizing,
                    'end_zone_timestep_after_zone_reporting': runtime.callback_end_zone_timestep_after_zone_reporting,
                    'end_zone_timestep_before_zone_reporting': runtime.callback_end_zone_timestep_before_zone_reporting,
                    'inside_system_iteration_loop': runtime.callback_inside_system_iteration_loop,
                    'register_external_hvac_manager': runtime.callback_register_external_hvac_manager,
                    'unitary_system_sizing': runtime.callback_unitary_system_sizing,
                }.items()
            },
        }
    
    @_functools_.cached_property
    def _std_callback_setters(self):
        class _Dispatcher:
            def __init__(self, event: Event):
                self._event = event

            def _state(self, *args, **kwargs):
                self._event.__call__(
                    Context(
                        event=self._event,
                    ),
                )

        return {
            'begin': lambda event: self._core.hooks['run:pre'].on(
                _Dispatcher(event)._state,
            ),
            'end': lambda event: self._core.hooks['run:post'].on(
                _Dispatcher(event)._state,
            ),
        }
    
    # TODO rich format
    # TODO this is available names???
    def available_keys(self):
        return self._core_callback_setters.keys() | self._std_callback_setters.keys()
    
    # TODO this sucks!!!!!
    def __contains__(self, ref):
        # TODO accept Event.Refs!!!!!
        name = Event.Ref.copyof(ref).name
        return name in set(self.available_keys()) | set(['begin', 'end', 'timestep'])
    
    def __missing__(self, ref):
        r"""
        TODO doc

        This synchronizes the event manager with the core.
        """
        
        match ref:
            case 'timestep':
                return self['begin_zone_timestep_after_init_heat_balance']
            
        event = Event(ref=Event.Ref.copyof(ref))

        if event.ref.name in self._std_callback_setters:
            self._std_callback_setters[event.ref.name](event)
        elif event.ref.name in self._core_callback_setters:
            # TODO !!!!!!
            @self._core.hooks['run:pre'].on
            def _core_setup(*args, **kwargs):
                # TODO 
                self._core_callback_setters[event.ref.name](event)
            _core_setup()
        else:
            raise KeyError(f'Unknown event: {event.ref.name}')
        
        self._callbacks[ref] = event.__attach__(self)
        return self._callbacks[ref]
    
    def __getitem__(self, ref):
        if ref not in self._callbacks:
            return self.__missing__(ref)
        return self._callbacks[ref]

    def __delitem__(self, ref):
        raise NotImplementedError
        # TODO rm setup
        # TODO rm `setup` when no listeners
        return super().__delitem__(ref)
    
    # TODO standardize: warn abt self[ref](...) as alt, 
    # or use EventQueue inplace of CallbackPipeline !!!!!
    def __call__(self, ref, context: Context):
        return super().__call__(
            ref, 
            Context.copyof(
                context, 
                event=self[ref],
            ),
        )

    # TODO
    # def __getstate__(self) -> object:
    #     return super().__getstate__()
    
    # def __setstate__(self, state: object):
    #     return super().__setstate__(state)


__all__ = [
    'Event',
    'EventManager',
]
