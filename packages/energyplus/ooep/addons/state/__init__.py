import contextlib
import typing

import threading

from ... import ems
from . import callback_queues


class BaseStateMachine:
    class StepFunction:
        def __init__(
            self, 
            state_machine: 'BaseStateMachine',
            event_specs: ems.Environment.Event.Specs
        ):
            self._callback = callback_queues.CloseableCallbackQueue()
            self._state_machine = state_machine
            self._event_specs = event_specs
        
        @contextlib.contextmanager
        def __state_context__(self):
            self._state_machine._env.event_listener.subscribe(
                self._event_specs,
                self._callback,
            )
            yield
            self._callback.close()

        def __call__(self, func: typing.Callable | None = None):
            return self._callback.call(func)

    def __init__(
        self, 
        env: ems.Environment
    ):
        self._env = env
        self._step_funcs: typing.List[self.StepFunction] = []

    def step_function(self, event_specs):
        f = self.StepFunction(self, event_specs)
        self._step_funcs.append(f)
        return f

    def run_blocking(self, *args, **kwargs):
        with contextlib.ExitStack() as stack:
            for f in self._step_funcs:
                stack.enter_context(f.__state_context__())
            return self._env(*args, **kwargs)

class StateMachine(BaseStateMachine):
    def run(self, *args, **kwargs):
        thr = threading.Thread(
            target=self.run_blocking, 
            args=args, kwargs=kwargs,
        )
        thr.start()


__all__ = [
    BaseStateMachine,
    StateMachine,
]
