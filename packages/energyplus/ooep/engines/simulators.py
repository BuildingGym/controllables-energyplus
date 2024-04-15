from __future__ import annotations

from .. import (
    components as _components_,
)

from . import base as _base_


class Simulator(_base_.Engine):
    def __init__(self):
        # TODO AddonManager?
        super().__init__()
        self._events = _components_.events.EventManager().__attach__(self)
        self._variables = _components_.variables.VariableManager().__attach__(self)
        self._awaitable = _components_.views.AwaitableView().__attach__(self)

    @property
    def events(self):
        return self._events

    @property
    def variables(self):
        return self._variables
    
    @property
    def awaitable(self):
        return self._awaitable


__all__ = [
    'Simulator',
]