r"""
TODO
"""


import functools as _functools_
import warnings as _warnings_
from typing import (
    Any,
    Generic,
    Literal,
    NamedTuple,
    Optional,
    SupportsFloat,
    TypedDict,
    Unpack,
)

from ...errors import OptionalModuleNotFoundError
try: 
    import pettingzoo as _pettingzoo_
    import pettingzoo.utils as _pettingzoo_utils_
    from pettingzoo.utils.env import AgentID, ObsType, ActionType
except ModuleNotFoundError as e:
    raise OptionalModuleNotFoundError.suggest(['pettingzoo']) from e

from ...callbacks import Callback
from ..gymnasium.agent import BaseAgentManager, AgentManager


# TODO
class _TypedAECEnv(
    Generic[AgentID, ObsType, ActionType],
    _pettingzoo_.AECEnv[AgentID, ObsType, ActionType],
):
    pass


# TODO
class BaseAECEnv(_TypedAECEnv, BaseAgentManager):
    pass


# TODO !!!!!
class AECEnv(
    Generic[AgentID, ObsType, ActionType],
    _pettingzoo_.AECEnv[AgentID, ObsType, ActionType],
):
    r"""
    TODO
    """

    def __init__(self):
        super().__init__()

    # TODO
    @_functools_.cached_property
    def _agent_selector(self):
        return _pettingzoo_utils_.agent_selector(self.agents)


class _TypedParallelEnv(
    Generic[AgentID, ObsType, ActionType],
    _pettingzoo_.ParallelEnv[AgentID, ObsType, ActionType],
):
    r"""TODO"""

    class StepResult(NamedTuple):
        observations: dict[AgentID, ObsType]
        rewards: dict[AgentID, SupportsFloat]
        terminations: dict[AgentID, bool]
        truncations: dict[AgentID, bool]
        infos: dict[AgentID, dict[str, Any]]

    def step(
        self,
        actions: dict[AgentID, ActionType],
    ) -> StepResult:
        return super().step(actions=actions)
    
    class ResetResult(NamedTuple):
        observations: dict[AgentID, ObsType]
        infos: dict[AgentID, dict]

    def reset(
        self,
        seed: int | None = None,
        options: dict | None = None,
    ) -> ResetResult:
        return super().reset(seed=seed, options=options)


# TODO
class BaseParallelEnv(_TypedParallelEnv, BaseAgentManager):
    r"""
    Gymnasium-compliant environment for interfacing with :class:`BaseSystem`s.
    """

    # TODO !!!!!!
    metadata: dict[str, Any]
    r"""(IMPLEMENT) TODO"""

    agents: list[AgentID]
    r"""(IMPLEMENT) TODO"""

    possible_agents: list[AgentID]
    r"""(IMPLEMENT) TODO"""

    class EventSources(TypedDict):
        step: Optional[Callback]
        r"""
        An event occurrence that corresponds to 
        a step (state transition) in this environment.

        This can be:
            * A :class:`Callback` object, whose call 
                signals the environment's state transition.
            * :class:`None`, indicating no event to wait for.

        .. seealso: :meth:`BaseParallelEnv.step`
        """

    event_sources: EventSources
    r"""(IMPLEMENT) TODO Event sources."""
    
    @property
    def observation_spaces(self):
        return super().observation_spaces
    
    @property
    def action_spaces(self):
        return super().action_spaces
    
    def observation_space(self, agent):
        return self.observation_spaces[agent]
    
    def action_space(self, agent):
        return self.action_spaces[agent]

    def step(self, actions):
        r"""
        TODO doc
        Every call to :meth:`step` will wait for this event to be triggered.
        """

        self.actions.value = actions

        finalize = None
        if (event := self.event_sources.get('step', None)) is not None:
            finalize = event.wait(deferred=True).ack

        try:
            res = self.StepResult(
                observations=self.observations.value,
                rewards=self.rewards.value,
                terminations=self.terminations.value, # TODO when?
                truncations=self.truncations.value,
                infos=self.infos.value,
            )
        except Exception as e:
            raise e
        finally:
            if finalize is not None: 
                finalize()
        return res

    def reset(self, *, seed=None, options=None):
        return self.ResetResult(
            observations=self.observations.value,
            infos=self.infos.value,
        )
    
    
class ParallelEnv(BaseParallelEnv, AgentManager):
    class Config(AgentManager.Config):
        event_sources: Optional[dict[Literal['step'], Callback]]

    def __init__(self, config: Config = Config(), **kwds: Unpack[Config]):
        config = self.Config({**config, **kwds})
        super().__init__(config=config)
        self.event_sources = self.EventSources(
            config.pop('event_sources', None) or dict()
        )

    @property
    def possible_agents(self):
        return super().refs

    @property
    def agents(self):
        r"""TODO doc!!!"""
        return self.possible_agents


__all__ = [
    'BaseParallelEnv',
    'ParallelEnv',
]