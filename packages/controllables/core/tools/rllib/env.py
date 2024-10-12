r"""
TODO
"""


import abc as _abc_
import functools as _functools_
import warnings as _warnings_
from typing import Callable, Unpack, Optional, TypedDict

try: 
    from ray.rllib.env import ExternalEnv, ExternalMultiAgentEnv
except ModuleNotFoundError as e:
    from ...errors import OptionalModuleNotFoundError
    raise OptionalModuleNotFoundError.suggest(['ray[rllib]']) from e

from ..gymnasium.agent import Agent, AgentManager
from ...callbacks import Callback
from ...components import BaseComponent
from ...errors import TemporaryUnavailableError, TemporaryUnavailableWarning
from ...refs import Derefable, bounded_deref
from ...systems import BaseSystem


class _EnvHelperMixin(
    ExternalEnv, 
    BaseComponent[BaseSystem],
    _abc_.ABC,
):
    r"""
    Helper mixin for :class:`ExternalEnv`s.
    """

    @property
    def system(self):
        r"""Access to the attached system."""
        
        return self._manager

    @_abc_.abstractmethod
    def step_episode(self, episode_id: str, off_policy: bool = False) -> None:
        r"""
        (IMPLEMENT) Execute one step of the episode.

        The implementation typically should:
        1. Call :meth:`log_returns` to log the reward.
        2. Depending on the value of :param:`off_policy`:
            * If `True`, call :meth:`log_action` to _log_ the computed action.
            * If `False`, call :meth:`get_action` to _obtain_ the next action 
                and _perform_ it.

        :param episode_id: The episode ID.
        :param off_policy: Whether to perform this operation off-policy.
        """

        ...

    class EpisodeSchedule(TypedDict):
        begin: Optional[Callback | Derefable[Callback]]
        step: Optional[Callback | Derefable[Callback]]
        end: Optional[Callback | Derefable[Callback]]

    def schedule_episode(
        self, 
        episode_id: str | None = None,
        schedule: EpisodeSchedule = EpisodeSchedule(
            begin='begin', 
            step='timestep', 
            end='end',
        ),
        off_policy: bool = False,
    ):
        r"""
        Schedule an episode.
        TODO doc

        :param episode_id: The target episode ID.
        :param schedule: The episode schedule.
        :param off_policy: Whether this episode will be off-policy.
        :return: TODO
        """

        def _callback_of(o):
            return bounded_deref(self._manager.events, o, bound=Callback)
        
        def _unavailable_ignored(f: Callable):
            def f_wrapped(*args, **kwargs):
                try:
                    return f(*args, **kwargs)
                except TemporaryUnavailableError as e:
                    _warnings_.warn(e.warning(repr(f)))
            return f_wrapped
        
        def _action_queue_empty_ignored(f: Callable):
            import queue as _queue_

            def f_wrapped(*args, **kwargs):
                try:
                    return f(*args, **kwargs)
                except _queue_.Empty as e:
                    _warnings_.warn(
                        TemporaryUnavailableWarning(
                            'Timeout waiting for computed action from... '
                            'whoever responsible for serving it... '
                            'Is this you, '
                            '`ray.rllib._ExternalEnvEpisode.wait_for_action`?',
                            repr(f),
                            repr(e),
                        )
                    )
            return f_wrapped
        
        schedule = self.EpisodeSchedule(schedule)
        current_episode_id = None

        if 'begin' in schedule:
            @_callback_of(schedule['begin']).on
            @_unavailable_ignored
            def _(*args, **kwargs):
                nonlocal current_episode_id
                if current_episode_id is not None:
                    return
                current_episode_id = self.start_episode(episode_id)

        if 'step' in schedule:
            @_callback_of(schedule['step']).on
            @_unavailable_ignored
            @_action_queue_empty_ignored
            def _(*args, **kwargs):
                if current_episode_id is None:
                    return
                self.step_episode(
                    current_episode_id, 
                    off_policy=off_policy,
                )

        if 'end' in schedule:
            @_callback_of(schedule['end']).on
            @_unavailable_ignored
            def _(*args, **kwargs):
                nonlocal current_episode_id
                if current_episode_id is None:
                    return
                self.end_episode(current_episode_id)
                current_episode_id = None

        # TODO repeat? cancel? teardown?
        pass
    
    def run(self):
        r"""
        (IMPLEMENT) The run loop.

        The implementation typically should either:
        * Call :meth:`schedule_episode` to _schedule_ episodes with event sources.
        * -OR- Continously: 
            1. Call :meth:`start_episode` to _start_ an episode.
            2. (Repeatedly) call :meth:`step_episode` 
                to execute a _step_ in the episode.
            3. Call :meth:`end_episode` to _end_ the episode.

        The default implementation _schedules_ a single episode 
        and _waits_ for the :meth:`__attach__`ed system to finish.

        .. seealso:: 
        :meth:`ray.rllib.env.ExternalMultiAgentEnv.run`
        """

        self.schedule_episode()
        if not self.system.started:
            _warnings_.warn(
                f'{self!r}: Attached {self.system!r} not started. '
                f'The {self.run!r} loop may terminate prematurely',
                RuntimeWarning,
            )
        self.system.wait()


class Env(
    _EnvHelperMixin,
    ExternalEnv, 
    BaseComponent[BaseSystem], 
    _abc_.ABC,
):
    class Config(Agent.Config):
        pass

    @_functools_.cached_property
    def agent(self):
        return Agent(self.config)

    def __attach__(self, manager):
        super().__attach__(manager)
        self.agent.__attach__(manager)
        return self    

    def __init__(self, config: Config, **config_kwds: Unpack[Config]):
        r"""TODO docs"""

        self.config = self.Config(config, **config_kwds)
        super().__init__(
            action_space=self.agent.action_space, 
            observation_space=self.agent.observation_space,
        )
    
    def log_action(self, episode_id, observation=None, action=None):
        return super().log_action(
            episode_id, 
            observation=observation 
                if observation is not None else 
                self.agent.observation.value,
            action=action
                if action is not None else
                self.agent.action.value,
        )

    def get_action(self, episode_id, observation=None):
        return super().get_action(
            episode_id, 
            observation=observation 
                if observation is not None else
                self.agent.observation.value,
        )
        
    def log_returns(self, episode_id, reward=None, info=None):
        return super().log_returns(
            episode_id, 
            reward=reward 
                if reward is not None else 
                self.agent.reward.value, 
            info=info 
                if info is not None else 
                self.agent.info.value, 
        )
    
    def start_episode(self, episode_id=None, training_enabled=True):
        return super().start_episode(
            episode_id=episode_id, 
            training_enabled=training_enabled,
        )

    def end_episode(self, episode_id, observation=None):
        return super().end_episode(
            episode_id, 
            observation=observation
                if observation is not None else
                self.agent.observation.value,
        )
    
    def step_episode(self, episode_id, off_policy=False):
        self.log_returns(episode_id)
        if off_policy:
            self.log_action(episode_id)
        else:
            self.agent.action.value = self.get_action(episode_id)


class MultiAgentEnv(
    _EnvHelperMixin,
    ExternalMultiAgentEnv, 
    BaseComponent[BaseSystem],
    _abc_.ABC,
):
    class Config(AgentManager.Config):
        pass

    @_functools_.cached_property
    def agents(self):
        return AgentManager(self.config)

    def __attach__(self, system):
        super().__attach__(system)
        self.agents.__attach__(system)
        return self
    
    def __init__(self, config: Config, **config_kwds: Unpack[Config]):
        r"""TODO docs"""

        self.config = self.Config(config, **config_kwds)
        super().__init__(
            action_space=self.agents.action_spaces, 
            observation_space=self.agents.observation_spaces,
        )

    def log_action(
        self, 
        episode_id, 
        observation_dict=None, 
        action_dict=None,
    ):
        return super().log_action(
            episode_id, 
            observation_dict=observation_dict
                if observation_dict is not None else
                self.agents.observations.value, 
            action_dict=action_dict
                if action_dict is not None else
                self.agents.actions.value,
        )

    def get_action(self, episode_id, observation_dict=None):
        return super().get_action(
            episode_id, 
            observation_dict=observation_dict
                if observation_dict is not None else
                self.agents.observations.value,
        )
    
    def log_returns(
        self, 
        episode_id, 
        reward_dict=None, 
        info_dict=None, 
        multiagent_done_dict=None,
    ):
        return super().log_returns(
            episode_id, 
            reward_dict=reward_dict
                if reward_dict is not None else
                self.agents.rewards.value, 
            info_dict=info_dict
                if info_dict is not None else
                self.agents.infos.value, 
            # NOTE BUG ray rllib upstream
            # multiagent_done_dict=multiagent_done_dict
            #     if multiagent_done_dict is not None else
            #     self.agents.terminations.value,
        )

    def start_episode(self, episode_id=None, training_enabled=True):
        return super().start_episode(
            episode_id=episode_id, 
            training_enabled=training_enabled,
        )

    def end_episode(self, episode_id, observation_dict=None):
        return super().end_episode(
            episode_id, 
            observation_dict=observation_dict
                if observation_dict is not None else
                self.agents.observations.value,
        )

    def step_episode(self, episode_id: str, off_policy: bool = False):
        self.log_returns(episode_id)
        if off_policy:
            self.log_action(episode_id)
        else:
            self.agents.actions.value = self.get_action(episode_id)


__all__ = [
    'Env',
    'MultiAgentEnv',
]