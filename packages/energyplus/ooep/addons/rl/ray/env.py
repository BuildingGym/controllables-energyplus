from __future__ import annotations

import typing as _typing_
# TODO
#import dataclasses as _dataclasses_

from ... import base as _base_

# TODO optional import
import ray.rllib as _rayrl_
import ray.rllib.utils.typing as _rayrl_typing_



from .... import (
    components as _components_,
    engines as _engines_,
    exceptions as _exceptions_,
)

from .. import gymnasium as _internal_gym_



class SimulatorEnv(
    _rayrl_.ExternalEnv, 
    _internal_gym_.BaseThinEnv,
):
    class Config(_typing_.TypedDict):
        action_space: _internal_gym_.VariableSpace
        observation_space: _internal_gym_.VariableSpace
        # TODO not just obs?? StepContext??
        reward_function: _typing_.Callable[[_internal_gym_.core.ObsType], float]
        event_keys: _typing_.Iterable[_components_.events.Event.Specs]
        # TODO
        #simulator: _engines_.simulators.Simulator
        simulator_factory: _typing_.Callable[[], _engines_.simulators.Simulator]

    def __init__(self, config: Config | _rayrl_typing_.EnvConfigDict):
        super().__init__(
            action_space=config['action_space'], 
            observation_space=config['observation_space'], 
        )
        self.reward_function = config['reward_function']
        self.event_keys = list(config['event_keys'])

        # TODO !!!!!!!!!!!!!!!!!
        self.__attach__(engine=config['simulator_factory']())

    '''
    @property
    def action_space(self):
        return super(_rayrl_.ExternalEnv, self).action_space
    
    @property
    def observation_space(self):
        return super(_rayrl_.ExternalEnv, self).observation_space
    '''

    '''
    # TODO ensure async engine???
    def __attach__(self, engine):
        super(_internal_gym_.BaseThinEnv, self).__attach__(engine=engine)
        return self
    '''

    def run(self):
        # TODO
        class Episode:
            pass

        episode = None
        observation = None

        def _start(__event):
            nonlocal self, episode
            # TODO
            print('start', episode)        

            if episode is not None:
                return 
            episode = self.start_episode()

        def step(__event):
            nonlocal self, episode, observation
            # TODO
            #print('step', episode, observation)

            if episode is None:
                return 
            try:
                observation = self.observe()
                self.log_returns(episode, self.reward_function(observation))
                self.act(self.get_action(episode, observation=observation))
            except _exceptions_.TemporaryUnavailableError:
                pass
        
        def end(__event):
            nonlocal self, episode, observation
            # TODO
            print('end', episode, observation)

            if episode is None:
                return
            # TODO !!!!!!!!!!!!!!!
            try: observation = self.observe()
            except _exceptions_.TemporaryUnavailableError: pass
            self.end_episode(episode, observation=observation)
            episode = None

        def setup(__event=...):
            nonlocal self, _start, end, step
            # TODO
            self._engine._workflows \
                .on('run:pre', _start) \
                .on('run:post', end)
            for event_key in self.event_keys:
                self._engine._events.on(event_key, step)

        def teardown(__event):
            nonlocal self, _start, end, step
            # TODO
            for event_key in self.event_keys:
                self._engine._events.off(event_key, step)            
            self._engine._workflows \
                .off('run:post', end) \
                .off('run:pre', _start)
        
        setup()
        
        # TODO !!!!!!!!
        import threading as _threading_
        event = _threading_.Event()
        # TODO
        event.wait()
        



# TODO rllib.env.external_multi_agent_env.ExternalMultiAgentEnv

__all__ = [
    SimulatorEnv,
]