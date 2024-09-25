import pytest as _pytest_

from controllables.energyplus.systems import System
from energyplus.dataset.basic import dataset


class TestWorld:
    @_pytest_.fixture(autouse=True)
    def world(self):
        self._world = System(config={
            'building': dataset.models / '1ZoneUncontrolled.idf',
            'weather': dataset.weathers / 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'
        })

    def test_workflows(self):
        # TODO
        pass

    def test___getstate____setstate__(self):
        world_ = System()
        world_.__setstate__(self._world.__getstate__())
        assert self._world._config == world_._config

    def test_start_stop(self):
        self._world.start().wait()
        # world should already be stopped at this point
        with _pytest_.raises(RuntimeError):
            self._world.stop()

    @_pytest_.mark.asyncio
    async def test_awaitable(self):
        return
    
        # TODO
        await self._world.awaitable.run()
        # world should already be stopped at this point
        with _pytest_.raises(RuntimeError):
            await self._world.awaitable.stop()
    

__all__ = [
    'TestWorld',
]