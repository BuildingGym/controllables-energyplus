from __future__ import annotations

import typing as _typing_

from . import base as _base_
from .. import utils as _utils_


# TODO component???
class Event(_utils_.events.BaseEvent):
    Ref: _typing_.Type[_utils_.events.BaseEventRef] = str

    def __init__(self, ref: str):
        super().__init__()
        self._ref = ref

    @property
    def ref(self) -> str: 
        return self._ref

    # TODO __attach__???

class MessageEvent(Event):
    def __init__(self, ref: str, message: str):
        super().__init__(ref=ref)
        self.message = message

class ProgressEvent(Event):
    def __init__(self, ref: str, progress: float):
        super().__init__(ref=ref)
        # TODO NOTE perct
        self.progress = progress

class StateEvent(Event):
    pass

# TODO typing
class EventManager(
    _utils_.events.BaseEventManager, 
    _base_.Component,
):
    @property
    def _ep_callback_setters(self):
        # TODO NOTE energyplus currently does not take ret values??
        def trigger(*args, **kwargs):
            try: self.trigger(*args, **kwargs)
            except Exception as e:
                self._engine.stop()
                raise e

        api = self._engine._core.api.runtime
        state = self._engine._core.state
        return {
            # TODO
            'message': lambda ref: 
                api.callback_message(
                    state, lambda s: trigger(
                        MessageEvent(ref=ref, message=bytes.decode(s))
                    )
                ),
            'progress': lambda ref: 
                api.callback_progress(
                    state, lambda n: trigger(
                        ProgressEvent(ref=ref, progress=(n / 100))
                    )
                ),
            # TODO
            **{
                ref: lambda ref, __callback_setter=callback_setter: 
                    __callback_setter(
                        # TODO use the env
                        state, lambda _: trigger(StateEvent(ref=ref))
                    )
                for ref, callback_setter in {
                    'after_component_get_input': api.callback_after_component_get_input,
                    'after_new_environment_warmup_complete': api.callback_after_new_environment_warmup_complete,
                    'after_predictor_after_hvac_managers': api.callback_after_predictor_after_hvac_managers,
                    'after_predictor_before_hvac_managers': api.callback_after_predictor_before_hvac_managers,
                    'begin_new_environment': api.callback_begin_new_environment,
                    'begin_system_timestep_before_predictor': api.callback_begin_system_timestep_before_predictor,
                    'begin_zone_timestep_after_init_heat_balance': api.callback_begin_zone_timestep_after_init_heat_balance,
                    'begin_zone_timestep_before_init_heat_balance': api.callback_begin_zone_timestep_before_init_heat_balance,
                    'begin_zone_timestep_before_set_current_weather': api.callback_begin_zone_timestep_before_set_current_weather,
                    'end_system_sizing': api.callback_end_system_sizing,
                    'end_system_timestep_after_hvac_reporting': api.callback_end_system_timestep_after_hvac_reporting,
                    'end_system_timestep_before_hvac_reporting': api.callback_end_system_timestep_before_hvac_reporting,
                    'end_zone_sizing': api.callback_end_zone_sizing,
                    'end_zone_timestep_after_zone_reporting': api.callback_end_zone_timestep_after_zone_reporting,
                    'end_zone_timestep_before_zone_reporting': api.callback_end_zone_timestep_before_zone_reporting,
                    'inside_system_iteration_loop': api.callback_inside_system_iteration_loop,
                    'register_external_hvac_manager': api.callback_register_external_hvac_manager,
                    'unitary_system_sizing': api.callback_unitary_system_sizing,
                }.items()
            },
        }

    def on(self, ref: Event.Ref, *handlers):
        super().on(ref, *handlers)

        def setup(__event=...):
            nonlocal self, ref
            self._ep_callback_setters[ref](ref)

        setup()
        self._engine._workflows.on('run:pre', setup)

        return self

    # TODO
    def off(self, ref, *handlers):
        raise NotImplementedError
        super().off(ref, *handlers)
        return self

    # TODO rich format
    def available_keys(self) -> _typing_.Iterable[Event.Ref]:
        return self._ep_callback_setters.keys()
    
    # TODO sync
    def __attach__(self, engine):
        super().__attach__(engine=engine)
        # TODO
        #self._engine._workflows.on('run:pre')
        return self


__all__ = [
    MessageEvent,
    ProgressEvent,
    StateEvent,
    EventManager,
]