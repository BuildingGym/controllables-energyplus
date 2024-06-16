
import typing as _typing_

from energyplus.ooep.components.worlds import World
# TODO
#import dataclasses as _dataclasses_


# TODO optional import
import ray.rllib as _rayrl_
import ray.rllib.utils.typing as _rayrl_typing_



from .... import (
    components as _components_,
    exceptions as _exceptions_,
)
from ... import base as _base_
from .. import gymnasium as _internal_gym_



import threading as _threading_

import functools as _functools_



T = _typing_.TypeVar('T')


class ExternalEnv(
    _rayrl_.ExternalEnv, 
    _base_.Addon,
):
    r"""
    A Ray RLlib external environment for interfacing with worlds.

    Example usage:

    .. code-block:: python

        import numpy as _numpy_
        import gymnasium as _gymnasium_

        from energyplus.ooep.addons.rl.gymnasium.spaces import VariableBox
        from energyplus.ooep.addons.rl.ray import ExternalEnv

        from energyplus.ooep.components.variables import (
            Actuator,
            OutputVariable,
        )

        # NOTE create and start an `energyplus.ooep.World` instance here
        world = ...

        env = ExternalEnv(
            ExternalEnv.Config(
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
                reward_function=lambda reward_ctx: 1 / reward_ctx['obs']['temperature'],
                event_refs=[
                    'begin_zone_timestep_after_init_heat_balance',
                ],
            )
        ).__attach__(engine=world)

    TODO more examples

    TODO
    .. seealso::
        * `ray.rllib.ExternalEnv <https://docs.ray.io/en/latest/rllib/package_ref/env/external_env.html#rllib-env-external-env-externalenv>`_
    """

    class Context(_typing_.TypedDict):
        env: 'ExternalEnv'
        obs: _internal_gym_.core.ObsType

    class ContextFunction(
        _typing_.Protocol,
        _typing_.Generic[T],
    ):
        def __call__(self, context: 'ExternalEnv.Context') -> T:
            ...

    class Config(_typing_.TypedDict):
        action_space: _internal_gym_.VariableSpace
        observation_space: _internal_gym_.VariableSpace
        reward_function: 'ExternalEnv.ContextFunction[float]'
        info_function: _typing_.Optional['ExternalEnv.ContextFunction[dict]']
        world_ref: _typing_.Optional[
            _components_.worlds.Engine 
            | _typing_.Callable[[], _components_.worlds.Engine]
        ]
        world_mgmt_enabled: _typing_.Optional[bool]
        # TODO make optional
        event_refs: _typing_.Iterable[_components_.events.Event.Ref]

    def __init__(self, config: Config | _rayrl_typing_.EnvConfigDict):
        super().__init__(
            action_space=config['action_space'], 
            observation_space=config['observation_space'],
        )
        self.reward_function = config['reward_function']
        self.info_function = config.get('info_function')
        self.world_ref = config.get('world_ref')
        self.world_mgmt_enabled = config.get('world_mgmt_enabled', False)
        self.event_refs = list(config['event_refs'])

    @_functools_.cached_property
    def _thread_locker(self):
        return _threading_.Event()

    @_functools_.cached_property
    def _base_env(self):
        return _internal_gym_.ThinEnv(
            action_space=self.action_space,
            observation_space=self.observation_space,
        )
    
    def __attach__(self, engine: World):
        super().__attach__(engine)
        self._base_env.__attach__(engine=engine)
        return self

    def run(self):
        if self.world_ref is not None:
            self.__attach__(
                self.world_ref
                if isinstance(self.world_ref, _components_.worlds.Engine) else 
                self.world_ref()
            )

        episode = None
        observation = None

        def start(event):
            nonlocal self, episode
            # TODO rm
            #print('start', episode)

            if episode is not None:
                return 
            episode = self.start_episode()

        def step(event):
            nonlocal self, episode, observation

            if episode is None:
                return 
            try:
                observation = self._base_env.observe()
                context = self.Context(env=self, obs=observation)
                self.log_returns(
                    episode, 
                    reward=self.reward_function(context),
                    info=self.info_function(context) 
                        if self.info_function is not None else None,
                )
                self._base_env.act(action := self.get_action(episode, observation=observation))
                # TODO rm !!!!!!!!!!!!!!!
                #print('act', action)
            except _exceptions_.TemporaryUnavailableError: pass
        
        def end(event):
            nonlocal self, episode, observation
            # TODO rm
            #print('end', episode, observation)

            if episode is None:
                return
            
            # TODO !!!!!!!!!!!!!!!
            try: observation = self._base_env.observe()
            except _exceptions_.TemporaryUnavailableError: pass

            self.end_episode(episode, observation=observation)
            episode = None

        def setup(event):
            nonlocal self, start, end, step
            if not hasattr(self, '_engine'):
                return
            # TODO detachable workflow??
            self._engine._workflows \
                .on('run:pre', start) \
                .on('run:post', end)
            for event_ref in self.event_refs:
                self._engine.events.on(event_ref, step)
        
        setup(...)
        self._workflows.on('attach', setup)
        
        if self.world_mgmt_enabled:
            self.world.run()
        else: self._thread_locker.wait()

    def join(self, timeout: float | None = None) -> None:
        if self.world_mgmt_enabled:
            self.world.stop()
        else: self._thread_locker.set()
        return super().join(timeout)
    
    # TODO !!!!!
    @property
    def world(self):
        return self._engine

# TODO rllib.env.external_multi_agent_env.ExternalMultiAgentEnv

__all__ = [
    'ExternalEnv',
]