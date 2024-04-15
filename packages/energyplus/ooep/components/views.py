r"""
Views

Scope: Alternative, non-default views of a system, simulated or real-world.
"""

import asyncio as _asyncio_

from .. import (
    utils as _utils_,
    components as _components_,
)


class AwaitableView(_components_.base.Component):
    def run(self, *args, **kwargs):
        return _asyncio_.create_task(
            _utils_.awaitables.asyncify()
            (self._engine.run)(*args, **kwargs)
        )
    
    def run_forever(self, *args, **kwargs):
        return _asyncio_.create_task(
            _utils_.awaitables.asyncify()
            (self._engine.run_forever)(*args, **kwargs)
        )
    
    def stop(self, *args, **kwargs):
        return _asyncio_.create_task(
            _utils_.awaitables.asyncify()
            (self._engine.stop)(*args, **kwargs)
        )
    
    
__all__ = [
    'AwaitableView',
]