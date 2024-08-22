import pytest as _pytest_
from controllables.energyplus import world as _world_

from energyplus.dataset.basic import dataset


class TestWorld:
    @_pytest_.fixture(autouse=True)
    def world(self):
        self._world = _world_.World({'input': {
            'world': dataset.models / '1ZoneUncontrolled.idf',
            'weather': dataset.weathers / 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'
        }})

    def test_workflows(self):
        # TODO
        pass

    def test___getstate____setstate__(self):
        world_ = _world_.World()
        world_.__setstate__(self._world.__getstate__())
        assert self._world._specs == world_._specs

    def test_run_stop(self):
        self._world.run()
        # world should already be stopped at this point
        with _pytest_.raises(RuntimeError):
            self._world.stop()

    @_pytest_.mark.asyncio
    async def test_awaitable(self):
        await self._world.awaitable.run()
        # world should already be stopped at this point
        with _pytest_.raises(RuntimeError):
            await self._world.awaitable.stop()
    

__all__ = [
    'TestWorld',
]