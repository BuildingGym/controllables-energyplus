r"""
Environments.
"""


import abc as _abc_
import functools as _functools_
import warnings as _warnings_
from typing import (
    Any, 
    Callable,
    Generic, 
    NamedTuple,
    Optional,
    Protocol, 
    SupportsFloat,
    TypeAlias,
    TypeVar, 
    TypedDict,     
    Unpack,
)

from ...systems import BaseSystem 
from ...components import BaseComponent
from ...variables import (
    # TODO
    _ValT,
    BaseVariable, 
    BaseMutableVariable,
    CompositeVariable, 
    ComputedVariable,
    MutableCompositeVariable,
    MutableVariable,
)
from ...callbacks import Callback
from ...refs import Derefable, deref, BaseRefManager
from .spaces import Space, SpaceVariable, MutableSpaceVariable

from ...errors import OptionalModuleNotFoundError
try: 
    import gymnasium as _gymnasium_
    from gymnasium.core import (
        ActType, 
        ObsType,
    )
except ModuleNotFoundError as e:
    raise OptionalModuleNotFoundError.suggest(['gymnasium']) from e

# TODO rm
from .agent import *


# TODO rm
class _TODO_rm_Agent(
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
        def __call__(self, agent: '_TODO_rm_Agent') -> '_TODO_rm_Agent._ContextRetT':
            ...

    # TODO !!!!
    class ContextVariable(
        BaseVariable, 
        BaseComponent['Agent'],
        Generic[_ContextRetT],
    ):
        def __init__(self, ref: '_TODO_rm_Agent.ContextFunction[_TODO_rm_Agent._ContextRetT]'):
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
            '_TODO_rm_Agent.RewardFunction'
        ]
        r"""Reward function."""
        info_function: Optional[
            '_TODO_rm_Agent.InfoFunction'
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

    # TODO ComputedVariable
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


# TODO dynamic agents
class _TODO_rm_AgentManager(
    dict[_RefT := TypeVar('_RefT'), _TODO_rm_Agent],
    BaseComponent[BaseSystem],
    Generic[_RefT],
):
    r"""TODO"""

    class Config(TypedDict):
        action_space: dict[_RefT, Space[ActType]]
        r"""Action space."""
        observation_space: dict[_RefT, Space[ObsType]]
        r"""Observation space."""

        reward_function: Optional[dict[_RefT, _TODO_rm_Agent.ContextFunction[float]]]
        r"""Reward function."""
        info_function: Optional[dict[_RefT, _TODO_rm_Agent.ContextFunction[dict]]]
        r"""Info function."""

    def __init__(self, config: Config):
        super().__init__()

        self.update({
            agent_ref: _TODO_rm_Agent(config=_TODO_rm_Agent.Config(
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
class Env(_TypedEnv, _TODO_rm_Agent):
    r"""
    Gymnasium-compliant environment for interfacing with :class:`BaseSystem`s.
    """

    class Config(_TODO_rm_Agent.Config):
        r"""
        Environment configuration class.
        """

        class Events(TypedDict):
            r"""Event configuration class."""

            step: Optional[Callback | Derefable[Callback] | None]
            r"""
            Reference to an event in the :class:`BaseSystem` that 
            corresponds to a step (state transition) in this environment.

            This can be:
                * A :class:`Callback` object.
                * A reference to a :class:`Callback` object,
                    valid inside the attached :class:`BaseSystem`.
                * :class:`None`, indicating no event to wait for.
            
            If unspecified, the :class:`BaseSystem`'s `step` event 
            is used when present.

            .. seealso: :meth:`Env.step`
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
        r"""
        TODO doc
        Every call to :meth:`step` will wait for this event to be triggered.
        """

        if self.reward is None:
            raise RuntimeError(
                f'Reward (function) MUST be defined for {self} '
                f'to be `{self.step}`-able. See {self.Config} ({self.config})'
            )

        self.action.value = action

        event_ref = (
            self.config
                .get('events', {})
                .get(
                    'step',
                    'timestep' 
                    if 'timestep' in self._manager.events else 
                    None,
                )
        )
        finalize = None
        
        if event_ref is not None:
            event = (
                event_ref 
                if isinstance(event_ref, Callback) else 
                deref(self.__manager__.events, event_ref)
            )
            finalize = event.wait(deferred=True).ack

        try:
            res = self.StepResult(
                observation=self.observation.value,
                reward=self.reward.value,
                terminated=self.termination.value, # TODO when?
                truncated=self.truncation.value,
                info=self.info.value if self.info is not None else dict(),
            )
        except Exception as e:
            raise e
        finally:
            if finalize is not None: 
                finalize()
        return res

    def reset(self, *, seed=None, options=None):
        return self.ResetResult(
            observation=self.observation.value,
            info=self.info.value if self.info is not None else dict(),
        )


__all__ = [
    'BaseAgent',
    '_TODO_rm_Agent',
    '_TODO_rm_AgentManager',
    'Env',
]