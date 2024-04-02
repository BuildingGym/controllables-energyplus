import asyncio as _asyncio_

from .. import (
    utils as _utils_,
    components as _components_,
)


class AwaitableView(_components_.base.Component):
    async def run(self, *args, **kwargs):
        return _asyncio_.create_task(
            _utils_.awaitables.asyncify()
            (self._engine.run)(*args, **kwargs)
        )
    
    async def run_forever(self, *args, **kwargs):
        return _asyncio_.create_task(
            _utils_.awaitables.asyncify()
            (self._engine.run_forever)(*args, **kwargs)
        )
    
    async def stop(self, *args, **kwargs):
        return _asyncio_.create_task(
            _utils_.awaitables.asyncify()
            (self._engine.stop)(*args, **kwargs)
        )
    
    
__all__ = [
    AwaitableView,
]