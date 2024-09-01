r"""
TODO
"""


import abc as _abc_
import functools as _functools_
from typing import (
    Any, 
    Generic, 
    Protocol, 
    TypeAlias,
    TypeVar, 
    TypedDict, 
    NamedTuple,
    Optional,
    SupportsFloat,
)

from ...systems import BaseSystem 
from ...components import BaseComponent
from ...variables import (
    BaseVariable, 
    CompositeVariable, 
    MutableCompositeVariable,
    MutableVariable,
)
from ...callbacks import Callback
from ...refs import Derefable, deref
from .spaces import Space, SpaceVariable, MutableSpaceVariable

from ...errors import OptionalModuleNotFoundError
try: 
    import gymnasium as _gymnasium_
    from gymnasium.core import (
        ActType, 
        ObsType,
    )
except ImportError as e:
    raise OptionalModuleNotFoundError.suggest(['gymnasium']) from e


class BaseAgent(
    BaseComponent[BaseSystem],
    _abc_.ABC,
):
    r"""
    Minimal abstract class for interfacing between 
    :class:`BaseSystem`s and :class:`gymnasium.spaces.Space`s. 

    .. note::
        * Implementations shall have `action_space` and `observation_space` defined.
        * Any `fundamental space <https://gymnasium.farama.org/api/spaces/fundamental/#fundamental-spaces>`_
            within the defined `action_space` and `observation_space` 
            must be associated with a variable (i.e. :class:`BaseVariable` and :class:`BaseMutableVariable`) 
            or a variable reference (TODO link) from an engine.

    .. note:: TODO FIXME
        This class cannot be used as a `gymnasium.Env` alone; 
        rather, it's designed to be integrated with 
        a Gymnasium-compliant environment (e.g. `gymnasium.Env`) 
        as a "mixin" to ensure compatibility with EnergyPlus OOEP engines.

    .. seealso::
        * `gymnasium.spaces.Space <https://gymnasium.farama.org/api/spaces/#gymnasium.spaces.Space>`_
        * `gymnasium.Env.action_space <https://gymnasium.farama.org/api/env/#gymnasium.Env.action_space>`_
        * `gymnasium.Env.observation_space <https://gymnasium.farama.org/api/env/#gymnasium.Env.observation_space>`_
    """

    action_space: Space[ActType]
    r"""(IMPLEMENT) All possible actions."""
    observation_space: Space[ObsType]
    r"""(IMPLEMENT) All possible observations."""

    # TODO !!!!!
    def __attach__(self, manager):
        super().__attach__(manager=manager)

        # TODO impl
        if self.action.__manager__ is None:
            self.action.__attach__(self._manager.variables)
        if self.observation.__manager__ is None:
            self.observation.__attach__(self._manager.variables)

        return self
    
    @_functools_.cached_property
    def action(self):
        r"""TODO"""
        return MutableSpaceVariable(self.action_space)

    @_functools_.cached_property
    def observation(self):
        r"""TODO"""
        return SpaceVariable(self.observation_space)

    def act(self, action: ActType) -> ActType:
        r"""
        Submit an action to the attached engine.
        
        :param action: An action within the action space :attr:`action_space`.
        :return: The action seen by the enviornment. Identical to the `action` submitted.
        """

        self.action.value = action
        return action

    def observe(self) -> ObsType:
        r"""
        Obtain an observation from the attached engine.
        
        :return: An observation from the observation space :attr:`observation_space`.
        """

        return self.observation.value


class Agent(
    BaseAgent,
    BaseComponent[BaseSystem],
):
    r"""
    Agent for interfacing with :class:`BaseSystem`s.
    
    This is an implementation of its base class :class:`BaseAgent`.
    """

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
        def __init__(self, ref: 'Agent.ContextFunction[Agent._ContextRetT]'):
            super().__init__()
            self.ref = ref
        
        @property
        def value(self):
            return self.ref(agent=self._manager)

    class Config(TypedDict):
        r"""
        Configuration for the agent.
        """

        action_space: Space[ActType]
        r"""Action space."""
        observation_space: Space[ObsType]
        r"""Observation space."""

        reward_function: Optional[
            'Agent.RewardFunction'
        ]
        r"""Reward function."""
        info_function: Optional[
            'Agent.InfoFunction'
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

    RewardFunction: TypeAlias = ContextFunction[float]
    RewardVariable: TypeAlias = ContextVariable[float]

    @_functools_.cached_property
    def reward(self):
        reward_function = self.config.get('reward_function')
        if reward_function is None:
            return None
        return self.RewardVariable(reward_function).__attach__(self)
    
    InfoFunction: TypeAlias = ContextFunction[dict]
    InfoVariable: TypeAlias = ContextVariable[dict]

    @_functools_.cached_property
    def info(self):
        info_function = self.config.get('info_function')
        if info_function is None:
            return None
        return self.InfoVariable(info_function).__attach__(self)


class AgentManager(
    dict[_RefT := TypeVar('_RefT'), Agent],
    BaseComponent[BaseSystem],
    Generic[_RefT],
):
    r"""TODO"""

    class Config(TypedDict):
        action_space: dict[_RefT, Space[ActType]]
        r"""Action space."""
        observation_space: dict[_RefT, Space[ObsType]]
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


class _TypedEnv(_gymnasium_.Env):
    r"""TODO"""

    class StepResult(NamedTuple):
        observation: ObsType
        reward: SupportsFloat
        terminated: bool
        truncated: bool
        info: dict[str, Any]

    def step(self, action: ActType) -> StepResult:
        return super().step(action=action)
    
    class ResetResult(NamedTuple):
        observation: ObsType
        info: dict[str, Any]
    
    def reset(
        self, 
        *, 
        seed: int | None = None, 
        options: dict[str, Any] | None = None,
    ) -> ResetResult:
        return super().reset(seed=seed, options=options)
    

# TODO NOTE gymnasium.Env is single-agent
class Env(_TypedEnv, Agent):
    r"""
    Gymnasium-compliant environment for interfacing with :class:`BaseSystem`s.
    """

    class Config(Agent.Config):
        r"""
        Environment configuration class.
        """

        class Events(TypedDict):
            r"""Event configuration class."""

            step: Optional[Callback | Derefable[Callback] | None]
            r"""
            Reference to an event that 
            triggers a step within this environment.
            """

        events: Optional[Events | None]
        r"""Events."""

    config: Config

    def __init__(self, config: Config):
        super().__init__(config=config)

    @_functools_.cached_property
    def termination(self):
        return MutableVariable(value=False)
    
    @_functools_.cached_property
    def truncation(self):
        return MutableVariable(value=False)

    def step(self, action):
        if self.reward is None:
            raise RuntimeError(
                f'Reward (function) MUST be defined for {self} '
                f'to be `{self.step}`-able. See {self.Config} ({self.config})'
            )

        self.action.value = action

        event_ref = (
            self.config
                .get('events', {})
                .get('step', None)
        )
        ack = None
        if event_ref is not None:
            event = (
                event_ref 
                if isinstance(event_ref, Callback) else 
                deref(self.__manager__.events, event_ref)
            )
            ack = event.wait(deferred=True).ack

        res = self.StepResult(
            observation=self.observation.value,
            reward=self.reward.value,
            terminated=self.termination.value, # TODO when?
            truncated=self.truncation.value,
            info=self.info.value if self.info is not None else dict(),
        )
        if ack is not None: ack()
        return res

    def reset(self, *, seed=None, options=None):
        return self.ResetResult(
            observation=self.observation.value,
            info=self.info.value if self.info is not None else dict(),
        )


__all__ = [
    'BaseAgent',
    'Agent',
    'AgentManager',
    'Env',
]