r"""
Events

Scope: Event management for the world.

.. seealso:: :mod:`..specs.callbacks`
"""


import typing as _typing_
import functools as _functools_
import dataclasses as _dataclasses_

from typing import Callable

from . import world as _world_

from ..specs.callbacks import Callback, CallbackManager
from ..specs.components import BaseComponent


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
    

EventCallable = Callable[[Context], _typing_.Any]

@_dataclasses_.dataclass
class Event(
    Callback[EventCallable],
    BaseComponent['EventManager'],
):
    r"""
    A generic event.
    """

    class Ref(_typing_.NamedTuple):
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

    ref: RefT | None = None
    r"""The reference to an event."""

    def __call__(self, *args, **kwargs):
        if self.ref is not None:
            if not Event.Ref.copyof(self.ref).include_warmup:
                if self._manager is None:
                    raise RuntimeError(
                        f'`include_warmup` specified in {self.ref} '
                        f'but no manager {self.__attach__}-ed'
                    )
                if self._manager._core.api \
                    .exchange.warmup_flag(self._manager._core.state):
                    return None

        return super().__call__(*args, **kwargs)


class EventManager(
    CallbackManager[
        Event.RefT, 
        EventCallable,
    ],
    BaseComponent[_world_.World],
):
    r"""
    Event manager.

    TODOs:
        * TODO sync w core; 
        * TODO child subeventmanager
    """

    def __getstate__(self) -> object:
        return super().__getstate__()
    
    def __setstate__(self, state: object):
        return super().__setstate__(state)
    
    @property
    def _core(self):
        return self._manager._core
    
    # TODO assoc defaultdict!!!!!!!
    @property
    def _core_callback_setters(self):
        r"""
        Callback setters for the core.
        """

        runtime = self._core.api.runtime
        state = self._core.state

        class _Dispatcher(BaseComponent[EventManager]):
            r"""
            Dispatcher for a reference in this event manager.
            All methods here are designed to be called by the core,
            which in turn would emit the respective events 
            in the event manager.
            """

            def __init__(self, ref: Event.RefT):
                r"""
                Initialize the dispatcher.
                
                :param ref: The reference to the event.
                """

                super().__init__()
                self._ref = ref

            def _message(self, m):
                r"""
                Callback for :class:`MessageContext`s.

                :param m: The message.

                .. seealso:: 
                    https://energyplus.readthedocs.io/en/latest/runtime.html#runtime.Runtime.callback_message
                """

                self._manager.__call__(
                    self._ref, 
                    MessageContext(message=bytes.decode(m)),
                )

            def _progress(self, p):
                r"""
                Callback for :class:`ProgressContext`s.

                :param p: The progress.

                .. seealso::
                    https://energyplus.readthedocs.io/en/latest/runtime.html#runtime.Runtime.callback_progress
                """

                self._manager.__call__(
                    self._ref, 
                    ProgressContext(progress=p / 100),
                )

            def _state(self, _):
                r"""
                Callback for :class:`Context`s.

                :param _: The core state, currently unused.
                :param ref: The reference to the event.

                .. seealso::
                    https://energyplus.readthedocs.io/en/latest/runtime.html
                """

                # TODO use the _ to identify the dispatcher
                self._manager.__call__(
                    self._ref, 
                    Context(),
                )

        def _ensure_exc(cb: Callable):
            @_functools_.wraps(cb)
            def cb_(*args, **kwargs):
                try:
                    return cb(*args, **kwargs)
                except Exception as e:
                    self._manager.stop()
                    raise e
            return cb_

        dispatch_for = lambda ref: _Dispatcher(ref=ref).__attach__(self)

        return {
            # message
            'message': lambda ref: 
                runtime.callback_message(
                    state, 
                    _ensure_exc(dispatch_for(ref)._message),
                ),
            # progress
            'progress': lambda ref: 
                runtime.callback_progress(
                    state, 
                    _ensure_exc(dispatch_for(ref)._progress),
                ),
            # state
            **{
                ref: lambda ref, callback_setter=callback_setter: 
                    callback_setter(
                        state, 
                        _ensure_exc(dispatch_for(ref)._state),
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
    
    # TODO rich format
    def available_keys(self):
        return self._core_callback_setters.keys()
    
    def __missing__(self, ref):
        r"""
        TODO doc

        This synchronizes the event manager with the core.
        """

        self[ref] = Event(ref=ref).__attach__(self)

        def setup(_=None):
            self._core_callback_setters[ref](ref)

        setup()
        self._manager.workflows.on('run:pre', setup)

        return self[ref]

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


__all__ = [
    'EventCallable',
    'Event',
    'EventManager',
]
