r"""

"""


import functools as _functools_

from controllables.core import (
    BaseComponent,
    BaseSystem,
    TemporaryUnavailableError,
)
from controllables.core.specs.variables import RefType, VariableRefManager
from controllables.core.tools.history import History
# TODO
from ..events import Event


# TODO typing!!!! TODO 
class VariableLogger(History, BaseComponent[BaseSystem]):
    class RefManager(BaseComponent[BaseSystem]):
        @_functools_.cached_property
        def _variables(self):
            return VariableRefManager()

        def __getitem__(self, ref):
            if ref in self._variables:
                return self._variables[ref]

            if self._manager is None:
                return None
            # TODO !!!!
            try:
                return self._manager.variables[ref].value
            except TemporaryUnavailableError:
                return None

    def __init__(self, spec, autoupdate: Event.RefT | None = None):
        super().__init__(spec, refs=self.RefManager())

        self._autoupdate = autoupdate

    _refs: 'VariableLogger.RefManager'

    def __attach__(self, manager):
        super().__attach__(manager)

        self._refs.__attach__(manager)

        if self._autoupdate is not None:
            def _update(_):
                self.poll()
            self._manager.events.on(self._autoupdate, _update)
        
        return self


__all__ = [
    'VariableHistory',
]
