r"""
Agent.
"""


import abc as _abc_
import contextlib as _contextlib_
import functools as _functools_
import warnings as _warnings_
from typing import (
    Any,
    Callable,
    Generic, 
    Optional,
    TypeVar, 
    TypedDict,     
    Unpack,
    Iterable,
)

try: 
    from gymnasium.core import (
        ActType, 
        ObsType,
    )
except ModuleNotFoundError as e:
    from ...errors import OptionalModuleNotFoundError
    raise OptionalModuleNotFoundError.suggest(['gymnasium']) from e

from ...systems import BaseSystem 
from ...components import Component
from ...variables import (
    # TODO
    ValT,
    BaseVariable, 
    BaseMutableVariable,
    CompositeVariable, 
    ComputedVariable,
    MutableCompositeVariable,
    MutableVariable,
)
from ...callbacks import Callback
from ...refs import ProtoRefManager, Derefable, bounded_deref
from .spaces import Space, SpaceVariable, MutableSpaceVariable


class BaseAgent(
    # TODO necesito?
    ProtoRefManager[Any, BaseVariable],
    Component['BaseSystem | BaseAgentManager'],
    _abc_.ABC,
):
    r"""
    Agent base class for :class:`BaseSystem`s 
    and :class:`BaseSystem`-attached :class:`BaseAgentManager`s.

    The agent is assumed to be both _controllable_ and _observable_.

    TODO doc
    .. note::
        * Implementations shall have `action_space` and `observation_space` defined.
        * Any `fundamental space <https://gymnasium.farama.org/api/spaces/fundamental/#fundamental-spaces>`_
        within or of the defined `action_space` and `observation_space` 
        must be associated with a variable through `bind`ing (TODO link). 

    """

    participation: BaseVariable[bool]
    r"""
    (IMPLEMENT) Participation.
    Controls agent participation in the environment;
    useful for dynamic multi-agent systems where agents 
    may only be active at certain times.
    """    

    action_space: Space[ActType]
    r"""
    (IMPLEMENT) All possible actions.

    .. seealso::
        * `gymnasium.Env.action_space <https://gymnasium.farama.org/api/env/#gymnasium.Env.action_space>`_
    """

    observation_space: Space[ObsType]
    r"""
    (IMPLEMENT) All possible observations.

    .. seealso::
        * `gymnasium.Env.observation_space <https://gymnasium.farama.org/api/env/#gymnasium.Env.observation_space>`_
    """

    reward: BaseVariable[float]
    r"""(IMPLEMENT) Reward variable."""

    info: BaseVariable[dict]
    r"""(IMPLEMENT) Info variable."""

    termination: BaseVariable[bool]
    r"""(IMPLEMENT) Termination variable."""

    truncation: BaseVariable[bool]
    r"""(IMPLEMENT) Truncation variable."""

    @property
    def system(self) -> BaseSystem | None:
        if self.__parent__ is None:
            return None
        if isinstance(self.__parent__, BaseSystem):
            return self.__parent__
        if isinstance(self.__parent__, BaseAgentManager):
            return self.__parent__.__parent__
        raise TypeError(f'Invalid manager type: {type(self.__parent__)}')
    
    def __getitem__(self, ref):
        return self.system.__getitem__(ref)
    
    def __contains__(self, ref):
        return self.system.__contains__(ref)
        
    @property
    def action(self) -> MutableSpaceVariable[ActType]:
        r"""
        The action :class:`BaseVariable` associated with :attr:`action_space`.
        The agent can be controlled by setting this variable
        with a value in :attr:`action_space`.
        """

        res = MutableSpaceVariable(self.action_space)
        # TODO attach to self
        if self.system is not None:
            #res.__attach__(self.system.variables)
            res.__attach__(self)
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
        # TODO attach to self
        if self.system is not None:
            #res.__attach__(self.system.variables)
            res.__attach__(self)
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
    
    @_contextlib_.contextmanager
    def commit(
        self, 
        action: ActType, 
        event_ref: Callback | Derefable[Callback] | None = None,
    ):
        r"""
        TODO doc

        Commit an action, wait for an event, and finalize when done.

        :param action: The action to commit.
        :param event_ref: 
            Reference to an event in the attached
            :class:`BaseSystem` that corresponds to 
            a "step" (state transition) for this agent.

            This can be:
            * A :class:`Callback` object.
            * A reference to a :class:`Callback` object,
                valid inside the attached :class:`BaseSystem`.
            * ```None```, indicating no event to wait for.
        """
        
        finalize = None
        try: 
            self.action.value = action
            if event_ref is not None:
                event = bounded_deref(
                    self.system.events, event_ref, 
                    bound=Callback,
                )
                finalize = event.wait(deferred=True).ack
            yield
        finally: 
            if finalize is not None: finalize()


_RefT = TypeVar('_RefT')
_AgentT = TypeVar('_AgentT', bound=BaseAgent)


class BaseAgentManager(
    Generic[_RefT, _AgentT],
    ProtoRefManager[_RefT, _AgentT],
    Component[BaseSystem],
    _abc_.ABC,
):
    r"""
    TODO doc
    Agent manager base class for :class:`BaseSystem`s.

    .. seealso::
        * :class:`BaseAgent`
    """

    refs: Iterable[_RefT]
    r"""(IMPLEMENT) All agent references."""

    @property
    def active_refs(self):
        r"""
        List of references to all participating agents.
        """
        
        return tuple(
            agent_ref
            for agent_ref in self.refs
            if self[agent_ref].participation.value
        )

    @property
    def participations(self):        
        return MutableCompositeVariable({
            agent_ref: self[agent_ref].participation
            for agent_ref in self.active_refs
        })
    
    @property
    def action_spaces(self):
        return {
            agent_ref: self[agent_ref].action_space
            for agent_ref in self.active_refs
        }

    @property
    def observation_spaces(self):
        return {
            agent_ref: self[agent_ref].observation_space
            for agent_ref in self.active_refs
        }
    
    @property
    def actions(self) -> BaseMutableVariable[dict[_RefT, ActType]]:
        return MutableCompositeVariable({
            agent_ref: self[agent_ref].action
            for agent_ref in self.active_refs
        })
    
    @property
    def observations(self) -> BaseMutableVariable[dict[_RefT, ObsType]]:
        return MutableCompositeVariable({
            agent_ref: self[agent_ref].observation
            for agent_ref in self.active_refs
        })

    @property
    def rewards(self) -> BaseMutableVariable[dict[_RefT, float]]:
        return MutableCompositeVariable({
            agent_ref: self[agent_ref].reward
            for agent_ref in self.active_refs
        })

    @property
    def infos(self) -> BaseMutableVariable[dict[_RefT, dict]]:
        return MutableCompositeVariable({
            agent_ref: self[agent_ref].info
            for agent_ref in self.active_refs
        })
    
    @property
    def terminations(self) -> BaseMutableVariable[dict[_RefT, bool]]:
        return MutableCompositeVariable({
            agent_ref: self[agent_ref].termination
            for agent_ref in self.active_refs
        })
    
    @property
    def truncations(self) -> BaseMutableVariable[dict[_RefT, bool]]:
        return MutableCompositeVariable({
            agent_ref: self[agent_ref].truncation
            for agent_ref in self.active_refs
        })
    

class Agent(BaseAgent):
    _MaybeComputedVariable = BaseVariable[ValT] | Callable[['Agent'], ValT]

    def _computed_variable(self, var: _MaybeComputedVariable):
        return (
            var 
            if isinstance(var, BaseVariable) else 
            ComputedVariable(var, self)
        )

    class Config(TypedDict):
        participation: Optional['Agent._MaybeComputedVariable[bool]']
        action_space: Space[ActType]
        observation_space: Space[ObsType]
        reward: Optional['Agent._MaybeComputedVariable[float]']
        info: Optional['Agent._MaybeComputedVariable[dict]']
        termination: Optional['Agent._MaybeComputedVariable[bool]']
        truncation: Optional['Agent._MaybeComputedVariable[bool]']

    def __init__(self, config: Config = dict(), **config_kwds: Unpack[Config]):
        self.__config__ = self.Config(config, **config_kwds)

    @_functools_.cached_property
    def participation(self) -> BaseVariable[bool]:
        if self.__config__.get('participation') is None:
            return MutableVariable(True)
        return self._computed_variable(self.__config__['participation'])
        
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
                f'{self!r} using default {default_var!r}. '
                f'Agent may have a constant reward unless '
                f'this variable is set manually'
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
                f'{self!r} using default {default_var!r}. '
                f'Agent may not terminate unless '
                f'this variable is set manually'
            )
            return default_var
        return self._computed_variable(self.__config__['termination'])
        
    @_functools_.cached_property
    def truncation(self) -> BaseVariable[bool]:
        if self.__config__.get('truncation') is None:
            return MutableVariable(False)
        return self._computed_variable(self.__config__['truncation'])


class AgentManager(
    BaseAgentManager[_RefT, _AgentT],
    Generic[_RefT, _AgentT],
):
    class Config(TypedDict):
        agents: Optional[dict[_RefT, Agent.Config]]
        action_spaces: Optional[dict[_RefT, Space[ActType]]]
        observation_spaces: Optional[dict[_RefT, Space[ObsType]]]
        rewards: Optional[dict[_RefT, Agent._MaybeComputedVariable[float]]]

    def __init__(self, config: Config = Config(), **config_kwds: Unpack[Config]):
        config = self.Config({**config, **config_kwds})

        for agent_ref in set.union(*[
            set(config.get(x, dict()).keys())
            for x in ('agents', 'action_spaces', 'observation_spaces', 'rewards')
        ]):
            agent_config = config.get('agents', dict()).get(agent_ref, dict())
            self.add(
                ref=agent_ref,
                agent=Agent({
                    **{
                        k: config.get(v, dict()).get(agent_ref)
                        for k, v in [
                            ('action_space', 'action_spaces'),
                            ('observation_space', 'observation_spaces'),
                            ('reward', 'rewards'),
                        ]
                    },
                    **agent_config,
                }),
            )

    @_functools_.cached_property
    def _data(self):
        return dict()
    
    def __iter__(self):
        return iter(self._data)
    
    # TODO typing not working?????
    def __getitem__(self, ref):
        return self._data[ref]
    
    def __contains__(self, ref):
        return ref in self._data
    
    @property
    def refs(self):
        return self._data.keys()

    def add(self, ref: _RefT, agent: _AgentT):        
        self._data[ref] = agent.attach(self)
        return self


__all__ = [
    'BaseAgent',
    'BaseAgentManager',
    'Agent',
    'AgentManager',
]