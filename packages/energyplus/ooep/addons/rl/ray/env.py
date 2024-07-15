r"""
TODO
"""


import abc as _abc_
import typing as _typing_
import functools as _functools_
import threading as _threading_

from typing import Generic, Protocol, TypeVar, TypedDict, Optional, TypeAlias, Self

from .... import (
    components as _components_,
)
from ... import base as _base_

from ..gymnasium.core import ObsType, BaseSpaceVariableContainer
from ..gymnasium.spaces import VariableSpace

try: 
    import ray.rllib.env as _rayrl_env_
    import ray.rllib.utils.typing as _rayrl_typing_
except ImportError as e:
    raise _base_.OptionalImportError.suggest(['ray[rllib]']) from e

try:
    from gymnasium.spaces import Space
except ImportError as e:
    raise _base_.OptionalImportError.suggest(['gymnasium']) from e


from ....components.events import Event

from ....specs.systems import BaseSystem 
from ....specs.exceptions import TemporaryUnavailableError
from ....specs.components import BaseComponent
from ....specs.variables import (
    BaseVariable, 
    BaseMutableVariable,
    CompositeVariable, 
    MutableCompositeVariable,
)
from ....specs.callbacks import Callback


class Agent(
    BaseSpaceVariableContainer,
    BaseComponent[BaseSystem],
):
    r"""Agent for interfacing with :class:`BaseSystem`s."""

    # TODO !!!!
    class ContextFunction(
        Protocol,
        Generic[_ContextRetT := TypeVar('_ContextRetT')],
    ):
        def __call__(self, agent: 'Agent') -> 'Agent._ContextRetT':
            ...

    # TODO !!!!
    class ContextVariable(
        BaseVariable, 
        BaseComponent['Agent'],
        Generic[_ContextRetT],
    ):
        ref: 'Agent.ContextFunction[Agent._ContextRetT]'
        
        @property
        def value(self):
            return self.ref(agent=self._manager)

    class Config(TypedDict):
        r"""
        Configuration for the agent.
        """

        action_space: Space[VariableSpace]
        r"""Action space."""
        observation_space: Space[VariableSpace]
        r"""Observation space."""

        reward_function: Optional[
            'Agent.ContextFunction[float]'
        ]
        r"""Reward function."""
        info_function: Optional[
            'Agent.ContextFunction[dict]'
        ]
        r"""Info function."""

    def __init__(self, config: Config):
        self.config = config

    @property
    def action_space(self):
        return self.config['action_space']
    
    @property
    def observation_space(self):
        return self.config['observation_space']

    @_functools_.cached_property
    def reward(self):
        reward_function = self.config.get('reward_function')
        if reward_function is None:
            return None
        return self.ContextVariable(reward_function).__attach__(self)
    
    @_functools_.cached_property
    def info(self):
        info_function = self.config.get('info_function')
        if info_function is None:
            return None
        return self.ContextVariable(info_function).__attach__(self)


class AgentManager(
    dict[_RefT := TypeVar('_RefT'), Agent],
    BaseComponent[BaseSystem],
    Generic[_RefT],
):
    r"""TODO"""

    class Config(TypedDict):
        action_space: dict[_RefT, Space[VariableSpace]]
        r"""Action space."""
        observation_space: dict[_RefT, Space[VariableSpace]]
        r"""Observation space."""

        reward_function: Optional[dict[_RefT, Agent.ContextFunction[float]]]
        r"""Reward function."""
        info_function: Optional[dict[_RefT, Agent.ContextFunction[dict]]]
        r"""Info function."""

    def __init__(self, config: Config):
        super().__init__()

        self.update({
            agent_ref: Agent(config=Agent.Config(
                action_space=config['action_space'][agent_ref],
                observation_space=config['observation_space'][agent_ref],
                reward_function=config['reward_function'].get(agent_ref)
                    if config.get('reward_function') is not None else None,
                info_function=config['info_function'].get(agent_ref)
                    if config.get('info_function') is not None else None,
            ))
            for agent_ref in config['action_space']
        })

    def __attach__(self, manager):
        super().__attach__(manager)

        for agent in self.values():
            agent.__attach__(self._manager)

        return self

    @property
    def actions(self):
        return MutableCompositeVariable({
            agent_ref: agent.action
            for agent_ref, agent in self.items()
        })
    
    @property
    def observations(self):
        return MutableCompositeVariable({
            agent_ref: agent.observation
            for agent_ref, agent in self.items()
        })

    @property
    def rewards(self):
        return CompositeVariable({
            agent_ref: agent.reward
            for agent_ref, agent in self.items()
        })

    @property
    def infos(self):
        return CompositeVariable({
            agent_ref: agent.info
            for agent_ref, agent in self.items()
        })


# TODO callback interface??
class BaseEnvEpisodeController(
    BaseComponent[
        _rayrl_env_.ExternalEnv 
        | _rayrl_env_.ExternalMultiAgentEnv
    ],
    _abc_.ABC,
):
    r"""
    
    .. code-block:: python
        env: ray.rllib.ExternalEnv = ...

        with env.track_episode() as episode:
            episode.step()

    """

    def __init__(self):
        self._episode_id = None

    @property
    def started(self):
        return self._episode_id is not None

    def start(self, training_enabled=True):

        if self._episode_id is not None:
            return 
        
        self._episode_id = self._manager.start_episode(
            training_enabled=training_enabled,
        )

        return self
    
    def end(self, observation=None):    
        if self._episode_id is None:
            return

        if isinstance(self._manager, _rayrl_env_.ExternalMultiAgentEnv):
            self._manager.end_episode(
                self._episode_id, 
                observation_dict=observation,
            )
        else:
            self._manager.end_episode(
                self._episode_id, 
                observation=observation,
            )
        self._episode_id = None

        return self

    def __enter__(self):
        return self.start()
    
    def __exit__(self, exc_type, exc_value, traceback):
        exc_type, exc_value, traceback
        return self.end()
    
    @_abc_.abstractmethod
    def step(self):
        ...

    def log_returns(
        self, 
        reward=None, info=None, 
    ):
        r"""
        TODO doc
        bail if no rewards
        """

        if self._episode_id is None:
            raise RuntimeError('TODO')

        if isinstance(self._manager, _rayrl_env_.ExternalMultiAgentEnv):
            return self._manager.log_returns(
                self._episode_id,
                reward_dict=reward,
                info_dict=info,
            )
        return self._manager.log_returns(
            self._episode_id,
            reward=reward,
            info=info,
        )
    
    def get_action(self, observation=None):
        r"""
        TODO doc
        bail if no observations
        """

        if self._episode_id is None:
            raise RuntimeError('TODO')

        if isinstance(self._manager, _rayrl_env_.ExternalMultiAgentEnv):
            return self._manager.get_action(
                self._episode_id, 
                observation_dict=observation,
            )
        return self._manager.get_action(
            self._episode_id, 
            observation=observation,
        )


class CommonEnv(
    _rayrl_env_.ExternalEnv,
    BaseComponent[BaseSystem],
    _abc_.ABC,
):
    class Config(_typing_.TypedDict):
        r"""
        Configuration for external environment 
        attached to a system.
        """

        system: _typing_.Optional[
            BaseSystem 
            | _typing_.Callable[[], BaseSystem]
        ]
        r"""
        Reference to the system to attach to.
        Can either be a system instance or 
        a callable that returns a system instance.
        If not specified, the system must be 
        :meth:`__attach__`-ed manually
        before anything can be done with the environment.

        .. seealso:: :meth:`ExternalEnv.__attach__`
        """
        system_mgmt_enabled: _typing_.Optional[bool]
        r"""
        Whether to manage the system internally - God mode.
        If :class:`True`, the environment will `start`/`stop` the system
        automatically when the environment is `run`/`join`-ed.

        Useful when the environment needs to be run in distributed settings,
        where the system cannot be shared among the nodes/workers.
        """

        class EpisodeEvents(_typing_.TypedDict):
            r"""Episode events."""

            RefT = Event.Ref | Callback

            start: _typing_.Optional[RefT | None]
            r"""Reference to start the episode."""

            end: _typing_.Optional[RefT | None]
            r"""Reference to end the started episode."""

            step: _typing_.Optional[RefT | None]
            r"""Reference to step the started episode."""

        episode_events: _typing_.Optional[EpisodeEvents]
        r"""Episode events."""

    def __init__(self, config: Config):
        self._config = config

    @_functools_.cached_property
    def _thread_locker(self):
        return _threading_.Event()
    
    @property
    @_abc_.abstractmethod
    def action(self) -> BaseMutableVariable | None: ...
    
    @property
    @_abc_.abstractmethod
    def observation(self) -> BaseVariable | None: ...

    @property
    @_abc_.abstractmethod
    def reward(self) -> BaseVariable | None: ...

    @property
    @_abc_.abstractmethod
    def info(self) -> BaseVariable | None: ...

    class EpisodeController(
        BaseEnvEpisodeController,
        BaseComponent['CommonEnv'],
    ):
        _manager: 'CommonEnv'

        def start(self, training_enabled=True):
            return super().start(
                training_enabled=training_enabled,
            )

        def end(self, observation=None):
            if observation is None:
                try: observation = self._manager.observation.value
                # TODO panic?????
                except TemporaryUnavailableError: pass
            return super().end(observation=observation)

        def step(self):
            if not self.started:
                return
            try:
                self.log_returns()
                if self._manager.action is not None:
                    self._manager.action.value = self.get_action()
            except TemporaryUnavailableError: pass

        def log_returns(self, reward=None, info=None):
            # TODO try/except
            if reward is None and self._manager.reward is not None:
                reward = self._manager.reward.value
            if info is None and self._manager.info is not None:
                info = self._manager.info.value
            return super().log_returns(reward=reward, info=info)
        
        def get_action(self, observation=None):
            if observation is None and self._manager.observation is not None:
                try: observation = self._manager.observation.value
                # TODO panic?????
                except TemporaryUnavailableError: pass
            return super().get_action(observation=observation)

    def episode_controller(self):
        r"""
        TODO doc
        """

        return self.EpisodeController().__attach__(self)

    def run(self):
        r"""
        TODO doc
        
        """

        if (system := self._config.get('system')) is not None:
            if isinstance(system, BaseSystem):
                self.__attach__(system)
            elif isinstance(system, _typing_.Callable):
                self.__attach__(system())
            else:
                raise TypeError(f'Invalid `{BaseSystem}` reference type: {type(system)}')

        def setup():
            if self._manager is None:
                raise RuntimeError(
                    f'Cannot run without a `{BaseSystem}` `{self.__attach__}`-ed'
                )
            
            episode_events: CommonEnv.Config.EpisodeEvents = {
                'start': self._manager.workflows['run:pre'],
                'end': self._manager.workflows['run:post'],
                'step': None,
                **self._config.get('episode_events', dict()),
            }

            def _get_callback(o) -> Callback:
                if isinstance(o, Callback):
                    return o
                return self._manager.events[o]

            # TODO bridge callbacks: .on(<Callback instance>)
            tracker = self.episode_controller()
            for key, callback in [
                ('start', lambda _, tracker=tracker: tracker.start()),
                ('end', lambda _, tracker=tracker: tracker.end()),
                ('step', lambda _, tracker=tracker: tracker.step()),
            ]:
                if episode_events.get(key) is not None:
                    _get_callback(episode_events[key]).on(callback)

        # TODO teardown afterwards OR subevent/subvariables!!!
        setup()
        # TODO self.__attach__.on(lambda _: setup())
        #self._TODO_workflows.on('attach', setup)
        
        if self._config.get('system_mgmt_enabled'):
            self._manager.run()
        else: self._thread_locker.wait()

    def join(self, timeout=None):
        r"""
        TODO doc
        
        """

        if self._config.get('system_mgmt_enabled'):
            self._manager.stop()
        else: self._thread_locker.set()
        return super().join(timeout=timeout)


# TODO !!!!
class ExternalMultiAgentEnv(
    CommonEnv,
    _rayrl_env_.ExternalMultiAgentEnv,
):
    class Config(AgentManager.Config, CommonEnv.Config):
        pass
        
    # TODO
    def __init__(self, config: Config):
        _rayrl_env_.ExternalMultiAgentEnv.__init__(
            self,
            action_space=config['action_space'],
            observation_space=config['observation_space'],
        )
        CommonEnv.__init__(self, config=config)
        self._agents = AgentManager(config)

    def __attach__(self, manager):
        CommonEnv.__attach__(self, manager)
        self._agents.__attach__(self._manager)
        return self
    
    @property
    def action(self): 
        return self._agents.actions
    @property
    def observation(self): 
        return self._agents.observations
    @property
    def reward(self): 
        return self._agents.rewards
    @property
    def info(self): 
        return self._agents.infos


# TODO
class ExternalEnv(
    CommonEnv,
    _rayrl_env_.ExternalEnv, 
):
    r"""
    A Ray RLlib external environment for interfacing with worlds.

    Examples:

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
                reward_function=lambda agent: 1 / agent.observation.value['temperature'],
                episode_events={
                    # TODO
                    'start': world.workflows['run:pre'],
                    'end': world.workflows['run:post'],
                    #'step': world.events['begin_zone_timestep_after_init_heat_balance'],
                    'step': 'begin_zone_timestep_after_init_heat_balance',
                },
            )
        ).__attach__(world)

    TODO more examples

    TODO
    .. seealso::
        * `ray.rllib.ExternalEnv <https://docs.ray.io/en/latest/rllib/package_ref/env/external_env.html#rllib-env-external-env-externalenv>`_
    """

    class Config(Agent.Config, CommonEnv.Config):
        pass
        
    # TODO
    def __init__(self, config: Config):
        _rayrl_env_.ExternalEnv.__init__(
            self,
            action_space=config['action_space'],
            observation_space=config['observation_space'],
        )
        CommonEnv.__init__(self, config=config)
        self._agents = AgentManager(AgentManager.Config(
            action_space={None: config['action_space']},
            observation_space={None: config['observation_space']},
            reward_function={None: config.get('reward_function')},
            info_function={None: config.get('info_function')},
        ))

    def __attach__(self, manager):
        CommonEnv.__attach__(self, manager)
        self._agents.__attach__(self._manager)
        return self
    
    @property
    def action(self): 
        return self._agents[None].action
    @property
    def observation(self): 
        return self._agents[None].observation
    @property
    def reward(self): 
        return self._agents[None].reward
    @property
    def info(self): 
        return self._agents[None].info


__all__ = [
    'ExternalMultiAgentEnv',
    'ExternalEnv',
]