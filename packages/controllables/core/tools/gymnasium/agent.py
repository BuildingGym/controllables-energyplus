r"""
Agent.
"""


import abc as _abc_
import functools as _functools_
import warnings as _warnings_
from typing import (
    Callable,
    Generic, 
    Optional,
    TypeVar, 
    TypedDict,     
    Unpack,
    Iterable,
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


class BaseAgent(
    # TODO necesito?
    BaseComponent[BaseSystem],
    _abc_.ABC,
):
    r"""
    TODO doc
    Base class for interfacing between 
    :class:`BaseSystem`s and :class:`gymnasium.spaces.Space`s. 

    The agent is assumed to be both _controllable_ and _observable_.

    .. note::
        * Implementations shall have `action_space` and `observation_space` defined.
        * Any `fundamental space <https://gymnasium.farama.org/api/spaces/fundamental/#fundamental-spaces>`_
            within the defined `action_space` and `observation_space` 
            must be associated with a variable (i.e. :class:`BaseVariable` and :class:`BaseMutableVariable`) 
            or a variable reference (TODO link) from an engine.

    .. note:: TODO FIXME
        This class cannot be used as a `gymnasium.Env` standalone; 
        rather, it's designed to be integrated with 
        a Gymnasium-compliant environment (e.g. `gymnasium.Env`) 
        as a "mixin" to ensure compatibility with :class:`BaseSystem`s.

    .. seealso::
        * `gymnasium.spaces.Space <https://gymnasium.farama.org/api/spaces/#gymnasium.spaces.Space>`_
        * `gymnasium.Env.action_space <https://gymnasium.farama.org/api/env/#gymnasium.Env.action_space>`_
        * `gymnasium.Env.observation_space <https://gymnasium.farama.org/api/env/#gymnasium.Env.observation_space>`_
    """

    action_space: Space[ActType]
    r"""(IMPLEMENT) All possible actions."""

    observation_space: Space[ObsType]
    r"""(IMPLEMENT) All possible observations."""

    reward: BaseVariable[float]
    r"""(IMPLEMENT) Reward variable."""

    info: BaseVariable[dict]
    r"""(IMPLEMENT) Info variable."""

    termination: BaseVariable[bool]
    r"""(IMPLEMENT) Termination variable."""

    truncation: BaseVariable[bool]
    r"""(IMPLEMENT) Truncation variable."""
    
    @property
    def action(self) -> MutableSpaceVariable[ActType]:
        r"""
        The action :class:`BaseVariable` associated with :attr:`action_space`.
        The agent can be controlled by setting this variable
        with a value in :attr:`action_space`.
        """

        res = MutableSpaceVariable(self.action_space)
        if self.__manager__ is not None:
            res.__attach__(self._manager.variables)
        return res
        
    @property
    def observation(self) -> SpaceVariable[ObsType]:
        r"""
        The observation :class:`BaseVariable` associated 
        with :attr:`observation_space`.
        The agent can be observed by reading this variable.
        The value is in :attr:`observation_space`.
        """

        res = SpaceVariable(self.observation_space)
        if self.__manager__ is not None:
            res.__attach__(self._manager.variables)
        return res
    
    # TODO deprecate?
    def act(self, action: ActType) -> ActType:
        r"""
        Submit an action to the attached engine.
        Shortcut for setting the :attr:`action` variable.
        
        :param action: An action within the action space :attr:`action_space`.
        :return: The action seen by the enviornment. Identical to the `action` submitted.
        """

        self.action.value = action
        return action

    # TODO deprecate?
    def observe(self) -> ObsType:
        r"""
        Obtain an observation from the attached engine.
        Shortcut for reading the :attr:`observation` variable.
        
        :return: An observation from the observation space :attr:`observation_space`.
        """

        return self.observation.value    


class BaseAgentManager(
    Generic[
        _RefT := TypeVar('_RefT'), 
        _AgentT := TypeVar('_AgentT', bound=BaseAgent),
    ],
    BaseRefManager[_RefT, _AgentT],
    BaseComponent[BaseSystem],
    _abc_.ABC,
):
    r"""
    TODO doc
    Agent manager base class.

    """

    refs: Iterable[_RefT]
    r"""(IMPLEMENT) All agent references."""

    # TODO !!!!! RefManager has NO ITER!!!@!!!!!!!!!
    @property
    def action_spaces(self):
        return {
            agent_ref: self[agent_ref].action_space
            for agent_ref in self.refs
        }

    @property
    def observation_spaces(self):
        return {
            agent_ref: self[agent_ref].observation_space
            for agent_ref in self.refs
        }
    
    @property
    def actions(self) -> BaseMutableVariable[dict[_RefT, ActType]]:
        return MutableCompositeVariable({
            agent_ref: self[agent_ref].action
            for agent_ref in self.refs
        })
    
    @property
    def observations(self) -> BaseMutableVariable[dict[_RefT, ObsType]]:
        return MutableCompositeVariable({
            agent_ref: self[agent_ref].observation
            for agent_ref in self.refs
        })

    @property
    def rewards(self) -> BaseMutableVariable[dict[_RefT, float]]:
        return MutableCompositeVariable({
            agent_ref: self[agent_ref].reward
            for agent_ref in self.refs
        })

    @property
    def infos(self) -> BaseMutableVariable[dict[_RefT, dict]]:
        return MutableCompositeVariable({
            agent_ref: self[agent_ref].info
            for agent_ref in self.refs
        })
    
    @property
    def terminations(self) -> BaseMutableVariable[dict[_RefT, bool]]:
        return MutableCompositeVariable({
            agent_ref: self[agent_ref].termination
            for agent_ref in self.refs
        })
    
    @property
    def truncations(self) -> BaseMutableVariable[dict[_RefT, bool]]:
        return MutableCompositeVariable({
            agent_ref: self[agent_ref].truncation
            for agent_ref in self.refs
        })
    

class Agent(BaseAgent):
    _MaybeComputedVariable = BaseVariable[_ValT] | Callable[['Agent'], _ValT]

    def _computed_variable(self, var: _MaybeComputedVariable):
        return (
            var 
            if isinstance(var, BaseVariable) else 
            ComputedVariable(var, self)
        )

    class Config(TypedDict):
        action_space: Space[ActType]
        observation_space: Space[ObsType]
        reward: Optional['Agent._MaybeComputedVariable[float]']
        info: Optional['Agent._MaybeComputedVariable[dict]']
        termination: Optional['Agent._MaybeComputedVariable[bool]']
        truncation: Optional['Agent._MaybeComputedVariable[bool]']

    def __init__(self, config: Config = dict(), **kwds: Unpack[Config]):
        self.__config__ = self.Config({**config, **kwds})

    @property
    def action_space(self):
        return self.__config__['action_space']
    
    @property
    def observation_space(self):
        return self.__config__['observation_space']

    @_functools_.cached_property
    def reward(self) -> BaseVariable[float]:
        if self.__config__.get('reward') is None:
            default_var = MutableVariable(0.)
            _warnings_.warn(
                f'Reward value function not defined: '
                f'{self} using default {default_var!r}'
            )
            return default_var
        return self._computed_variable(self.__config__['reward'])
    
    @_functools_.cached_property
    def info(self) -> BaseVariable[dict]:
        if self.__config__.get('info') is None:
            return MutableVariable(dict())
        return self._computed_variable(self.__config__['info'])
        
    @_functools_.cached_property
    def termination(self) -> BaseVariable[bool]:
        if self.__config__.get('termination') is None:
            default_var = MutableVariable(False)
            _warnings_.warn(
                f'Termination value function not defined: '
                f'{self} using default {default_var!r}'
            )
            return default_var
        return self._computed_variable(self.__config__['termination'])
        
    @_functools_.cached_property
    def truncation(self) -> BaseVariable[bool]:
        if self.__config__.get('truncation') is None:
            return MutableVariable(False)
        return self._computed_variable(self.__config__['truncation'])


class AgentManager(
    Generic[_RefT, _AgentT],
    BaseAgentManager[_RefT, _AgentT],
):
    class Config(TypedDict):
        agents: dict[_RefT, Agent.Config]

    def __init__(self, config: Config = dict(), **kwds: Unpack[Config]):
        config = self.Config({**config, **kwds})

        for agent_ref, agent_config in config['agents'].items():
            self.add(
                ref=agent_ref,
                agent=Agent(agent_config),
            )

    @_functools_.cached_property
    def _data(self):
        return dict()
    
    def __getitem__(self, ref):
        return self._data[ref]
    
    def __contains__(self, ref):
        return ref in self._data
    
    @property
    def refs(self):
        return self._data.keys()

    # TODO
    def add(self, ref: _RefT, agent: _AgentT):
        self._data[ref] = agent.__attach__(self._manager)
        return self


__all__ = [
    'BaseAgent',
    'BaseAgentManager',
    'Agent',
    'AgentManager',
]