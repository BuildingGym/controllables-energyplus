import pytest as _pytest_

from controllables.energyplus import examples
from controllables.energyplus.systems import System


class TestSystem:
    @_pytest_.fixture(autouse=True)
    def make_system(self):
        self.system = examples.systems.X1ZoneUncontrolled()

    def test___getstate____setstate__(self):
        system_n = System()
        system_n.__setstate__(self.system.__getstate__())
        assert self.system._config == system_n._config

    def test_start_stop(self):
        self.system.start().wait()
        # system should already be stopped at this point
        with _pytest_.raises(RuntimeError):
            self.system.stop()

    @_pytest_.mark.asyncio
    async def test_awaitable(self):
        return
    
        # TODO
        await self.system.awaitable.run()
        # world should already be stopped at this point
        with _pytest_.raises(RuntimeError):
            await self.system.awaitable.stop()
    

__all__ = [
    'TestSystem',
]