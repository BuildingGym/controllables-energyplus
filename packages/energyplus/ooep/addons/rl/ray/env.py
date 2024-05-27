# from __future__ import annotations

import typing as _typing_
# TODO
#import dataclasses as _dataclasses_

from ... import base as _base_

# TODO optional import
import ray.rllib as _rayrl_
import ray.rllib.utils.typing as _rayrl_typing_



from .... import (
    components as _components_,
    exceptions as _exceptions_,
)

from .. import gymnasium as _internal_gym_



class SimulatorEnv(
    _rayrl_.ExternalEnv, 
    _internal_gym_.BaseThinEnv,
):
    r"""
    A Ray RLlib external environment for interfacing with simulation engines.

    Example usage:

    .. code-block:: python

        import numpy as _numpy_
        import gymnasium as _gymnasium_

        from energyplus.ooep.addons.rl.gymnasium.spaces import VariableBox
        from energyplus.ooep.addons.rl.ray import SimulatorEnv

        from energyplus.ooep.components.variables import (
            Actuator,
            OutputVariable,
        )

        # NOTE create and start an `energyplus.ooep.World` instance here
        simulator = ...

        SimulatorEnv(
            SimulatorEnv.Config(
                action_space=_gymnasium_.spaces.Dict({
                    'thermostat': VariableBox(
                        low=15., high=16.,
                        dtype=_numpy_.float32,
                        shape=(),
                    ).bind(Actuator.Ref(
                        type='Zone Temperature Control',
                        control_type='Heating Setpoint',
                        key='CORE_MID',
                    ))
                }),
                observation_space=_gymnasium_.spaces.Dict({
                    'temperature': VariableBox(
                        low=-_numpy_.inf, high=+_numpy_.inf,
                        dtype=_numpy_.float32,
                        shape=(),
                    ).bind(OutputVariable.Ref(
                        type='People Air Temperature',
                        key='CORE_MID',
                    )),
                }),
                reward_function=lambda _: 1,
                event_refs=[
                    'begin_zone_timestep_after_init_heat_balance',
                ],
                simulator_factory=lambda simulator=simulator: simulator,
            )        
        )

    TODO
    .. seealso::
        * `ray.rllib.ExternalEnv <https://docs.ray.io/en/latest/rllib/package_ref/env/external_env.html#rllib-env-external-env-externalenv>`_
    """

    class Config(_typing_.TypedDict):
        action_space: _internal_gym_.VariableSpace
        observation_space: _internal_gym_.VariableSpace
        # TODO not just obs?? StepContext??
        reward_function: _typing_.Callable[[_internal_gym_.core.ObsType], float]
        event_refs: _typing_.Iterable[_components_.events.Event.Ref]
        # TODO
        #simulator: _engines_.simulators.World
        simulator_factory: _typing_.Callable[[], _components_.worlds.World]

    def __init__(self, config: Config | _rayrl_typing_.EnvConfigDict):
        super().__init__(
            action_space=config['action_space'], 
            observation_space=config['observation_space'], 
        )
        self.reward_function = config['reward_function']
        self.event_refs = list(config['event_refs'])

        # TODO !!!!!!!!!!!!!!!!!
        self.__attach__(engine=config['simulator_factory']())

    '''
    # TODO ensure async engine???
    def __attach__(self, engine):
        super(_internal_gym_.BaseThinEnv, self).__attach__(engine=engine)
        return self
    '''

    def run(self):
        episode = None
        observation = None

        def start(__event):
            nonlocal self, episode
            # TODO rm
            #print('start', episode)        

            if episode is not None:
                return 
            episode = self.start_episode()

        def step(__event):
            nonlocal self, episode, observation

            if episode is None:
                return 
            try:
                observation = self.observe()
                self.log_returns(episode, self.reward_function(observation))
                self.act(action := self.get_action(episode, observation=observation))
                # TODO rm !!!!!!!!!!!!!!!
                #print('act', action)
            except _exceptions_.TemporaryUnavailableError: pass
        
        def end(__event):
            nonlocal self, episode, observation
            # TODO rm
            #print('end', episode, observation)

            if episode is None:
                return
            
            # TODO !!!!!!!!!!!!!!!
            try: observation = self.observe()
            except _exceptions_.TemporaryUnavailableError: pass

            self.end_episode(episode, observation=observation)
            episode = None

        def setup():
            nonlocal self, start, end, step
            # TODO detachable workflow??
            self._engine._workflows \
                .on('run:pre', start) \
                .on('run:post', end)
            for event_ref in self.event_refs:
                self._engine.events.on(event_ref, step)
        
        setup()
        
        # # TODO !!!!!!!!
        import threading as _threading_
        event = _threading_.Event()
        event.wait()
        



# TODO rllib.env.external_multi_agent_env.ExternalMultiAgentEnv

__all__ = [
    'SimulatorEnv',
]