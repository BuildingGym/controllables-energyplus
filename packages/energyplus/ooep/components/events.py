r"""
Events

Scope: Event management for engines and worlds.
"""

import typing as _typing_

from . import (
    base as _base_,
    worlds as _worlds_,
)
from .. import utils as _utils_


# TODO naming!!!!!!!!!!!!!!!!
# TODO component???
class Event(_utils_.events.BaseEvent):
    Ref = _utils_.events.BaseEventRef

    class Spec(_typing_.NamedTuple):
        ref: 'Event.Ref'
        include_warmup: bool = False

    def __init__(self, spec: Spec):
        super().__init__()
        self.spec = spec

    @property
    def ref(self): 
        return self.spec.ref

    # TODO __attach__???

class MessageEvent(Event):
    r"""
    An event that represents a message.
    """

    Ref = str

    def __init__(self, spec, message: str):
        r"""
        Initialize a new instance of :class:`MessageEvent`.
        
        :param spec: The specification of the event.
        :param message: The message.
        """
        super().__init__(spec=spec)
        self.message = message

class ProgressEvent(Event):
    r"""
    An event that represents the progress of a process.
    """

    Ref = str

    def __init__(self, spec, progress: float):
        r"""
        Initialize a new instance of :class:`ProgressEvent`.

        :param spec: The specification of the event.
        :param progress: The progress of the event as a percentage between 0 and 1.
        """
        super().__init__(spec=spec)
        self.progress = progress

class StateEvent(Event):
    r"""
    An event that represents a state change.
    """
    
    Ref = str

# TODO typing
class EventManager(
    _utils_.events.BaseEventManager, 
    _base_.Component[_worlds_.Engine],
):
    @property
    def _core_callback_setters(self):
        runtime = self._engine._core.api.runtime
        state = self._engine._core.state

        def trigger(*args, **kwargs):
            r"""
            Wrapper for triggering events with return values ignored
            due to the core API not handling return values properly.
            """

            nonlocal self
            self.trigger(*args, **kwargs)

        return {
            # TODO
            'message': lambda spec: 
                runtime.callback_message(
                    state, lambda s: trigger(
                        MessageEvent(spec=spec, message=bytes.decode(s))
                    )
                ),
            'progress': lambda spec: 
                runtime.callback_progress(
                    state, lambda n: trigger(
                        ProgressEvent(spec=spec, progress=(n / 100))
                    )
                ),
            # TODO
            **{
                ref: lambda spec, callback_setter=callback_setter: 
                    callback_setter(
                        # TODO use the env
                        state, lambda _: trigger(StateEvent(spec=spec))
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

    def on(self, spec_or_ref: Event.Spec | Event.Ref, *handlers):
        spec = (
            spec_or_ref
            if isinstance(spec_or_ref, Event.Spec) else
            Event.Spec(spec_or_ref)
        )

        super().on(spec.ref, *handlers)

        def setup(__event=...):
            nonlocal self, spec
            self._core_callback_setters[spec.ref](spec)

        setup()
        self._engine._workflows.on('run:pre', setup)

        return self

    # TODO
    def off(self, ref, *handlers):
        raise NotImplementedError
        super().off(ref, *handlers)
        return self

    # TODO
    def trigger(self, event: Event, *args, **kwargs):
        if not event.spec.include_warmup:
            if self._engine._core.api \
                .exchange.warmup_flag(self._engine._core.state):
                return self
            
        try: super().trigger(event, *args, **kwargs)
        except Exception as e:
            self._engine.stop()
            raise e
        
        return self

    # TODO rich format
    def keys(self) -> _typing_.Iterable[Event.Ref]:
        return self._core_callback_setters.keys()
    
    # TODO sync; TODO child eventmanager
    def __attach__(self, engine):
        super().__attach__(engine=engine)
        # TODO
        #self._engine._workflows.on('run:pre', ...)
        return self
    
    def __getstate__(self) -> object:
        return super().__getstate__()
    
    def __setstate__(self, state: object):
        return super().__setstate__(state)


__all__ = [
    'MessageEvent',
    'ProgressEvent',
    'StateEvent',
    'EventManager',
]