r"""TODO"""


from controllables.energyplus import (
    World,
    #WeatherModel,
    #Report,
    Actuator,
    OutputVariable,
)

from energyplus.dataset.basic import dataset as _epds_

world = World(
    input=World.Specs.Input(
        world=(
            _epds_.models / 'ASHRAE901_OfficeLarge_STD2019_Denver_Chiller205_Detailed.idf'
        ),
        weather=(_epds_.weathers / 'USA_CO_Denver-Aurora-Buckley.AFB.724695_TMY3.epw'),
    ),
    output=World.Specs.Output(
        #report=('/tmp/ooep-report-9e1287d2-8e75-4cf5-bbc5-f76580b56a69'),
    ),
    runtime=World.Specs.Runtime(
        #recurring=True,
        #design_day=True,
    ),
)

from controllables.core.tools.gymnasium import (
    DictSpace,
    BoxSpace,
    Agent,
)

import gymnasium as _gymnasium_
import numpy as _numpy_


env = Agent(
    action_space=DictSpace({
        'thermostat': BoxSpace(
            low=15., high=20.,
            dtype=_numpy_.float32,
            shape=(),
        ).bind(lambda world: world[Actuator.Ref(
            type='Zone Temperature Control',
            control_type='Heating Setpoint',
            key='CORE_MID',
        )])
    }),    
    observation_space=DictSpace({
        'temperature': BoxSpace(
            low=-_numpy_.inf, high=+_numpy_.inf,
            dtype=_numpy_.float32,
            shape=(),
        ).bind(
            # NOTE output variables need to be accessed 
            # BEFORE the simulation starts for them to be
            # immediately available
            world[OutputVariable.Ref(
                type='People Air Temperature',
                key='CORE_MID',
            )]
        ),
    }),
).__attach__(world)


import asyncio as _asyncio_

async def controller():
    while True:
        try:
            ctx = await world.events[
                'end_zone_timestep_after_zone_reporting'
            ].awaitable(deferred=True)
        # in case this has been canceled...
        except _asyncio_.CancelledError:
            break
        print(
            world['wallclock'].value, 
            f'last_action={env.action.value}', 
            f'current_observation={env.observe()}',
        )
        env.act({'thermostat': 20})
        ctx.ack()

async def main():
    # enable progress reporting for the world
    world.add('logging:progress')
    # run the world
    world.awaitable.run()

    # make the controller run in background
    control_task = _asyncio_.create_task(controller())

    # (optional) cancel the controller after a run of the world
    await world.workflows['run:post']
    control_task.cancel()

_asyncio_.run(main())