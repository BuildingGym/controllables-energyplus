r"""
Environments.
"""


from typing import (
    Any, 
    NamedTuple,
    SupportsFloat,
)

from ...callbacks import Callback
from ...refs import Derefable, deref
from .agent import Agent

try: 
    import gymnasium as _gymnasium_
    from gymnasium.core import (
        ActType, 
        ObsType,
    )
except ModuleNotFoundError as e:
    from ...errors import OptionalModuleNotFoundError
    raise OptionalModuleNotFoundError.suggest(['gymnasium']) from e


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
    

class Env(_TypedEnv, Agent):
    r"""
    Gymnasium-compliant environment for interfacing with :class:`BaseSystem`s.
    """

    class Config(Agent.Config):
        r"""
        Environment configuration class.
        """
        
        pass

    config: Config

    def __init__(self, config: Config):
        super().__init__(config=config)

    def step(
        self, 
        action: ActType, 
        event_ref: Callback | Derefable[Callback] | None = 'timestep',            
    ):
        r"""
        
        TODO
        If unspecified, the :class:`BaseSystem`'s `timestep` event 
            is used when present.
        """

        with self.commit(action=action, event_ref=event_ref):
            return self.StepResult(
                observation=self.observation.value,
                reward=self.reward.value,
                terminated=self.termination.value, # TODO when?
                truncated=self.truncation.value,
                info=self.info.value if self.info is not None else dict(),
            )

    def reset(self, *, seed=None, options=None):
        return self.ResetResult(
            observation=self.observation.value,
            info=self.info.value if self.info is not None else dict(),
        )


__all__ = [
    'Env',
]