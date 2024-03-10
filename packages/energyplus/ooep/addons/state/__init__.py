import contextlib
import typing

import threading

from ... import ems
from . import callback_queues


class Terminated(Exception):
    pass

class BaseStateMachine:
    Terminated = Terminated
    
    class StepFunction:
        class Terminated(Terminated):
            pass
        
        def __init__(
            self, 
            state_machine: 'BaseStateMachine',
            event_specs: ems.Environment.Event.Specs,
            condition: typing.Callable[..., bool] = None,
        ):
            self._state_machine = state_machine
            self._event_specs = event_specs
            
            class ConditionalFunction:
                def __init__(
                    self, 
                    base: typing.Callable,
                    condition: typing.Callable[..., bool] = None,
                    default_result: typing.Any = None,
                ):
                    self._base = base
                    self._condition = condition
                    self._default_result = default_result

                def __call__(
                    self, 
                    *args: typing.Any, 
                    **kwargs: typing.Any,
                ) -> typing.Any | None:
                    if self._condition is not None:
                        if not self._condition(*args, **kwargs):
                            return self._default_result
                    return self._base(*args, **kwargs)

            self._callback = ConditionalFunction(
                callback_queues.CloseableCallbackQueue(),
                condition=condition,
            )

        @property
        def _env(self):
            return self._state_machine._env

        def subscribe(self):
            self._callback._base.open()
            return self._env.event_listener.subscribe(
                self._event_specs,
                self._callback,
            )
        
        def unsubscribe(self):
            res = self._env.event_listener.unsubscribe(
                self._event_specs,
                self._callback,
            )
            self._callback._base.close()
            return res

        @contextlib.contextmanager
        def __state_context__(self):
            self.subscribe()
            yield
            self.unsubscribe()

        def __call__(self, func: typing.Callable | None = None):
            try: return self._callback._base.call(func)
            except self._callback._base.Closed:
                raise self.Terminated()

    def __init__(
        self, 
        env: ems.Environment
    ):
        self._env = env
        self._step_funcs: typing.List[self.StepFunction] = []

    def step_function(self, event_specs, condition=None):
        self._step_funcs.append(
            f := self.StepFunction(
                self, 
                event_specs=event_specs, 
                condition=condition,
            )
        )
        f.subscribe()
        return f

    def run_blocking(self, *args, **kwargs):
        with contextlib.ExitStack() as stack:
            for f in self._step_funcs:
                stack.enter_context(f.__state_context__())
            return self._env(*args, **kwargs)

    def stop(self):
        self._env.stop()

class StateMachine(BaseStateMachine):
    @property
    def env(self):
        return self._env

    def run(self, *args, **kwargs):
        self._thread = threading.Thread(
            target=self.run_blocking, 
            args=args, kwargs=kwargs,
        )
        self._thread.start()

    @property
    def running(self):
        if not hasattr(self, '_thread'):
            return False
        return self._thread.is_alive()


__all__ = [
    Terminated,
    BaseStateMachine,
    StateMachine,
]
