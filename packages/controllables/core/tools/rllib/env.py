r"""
Environment.
"""


import abc as _abc_
import functools as _functools_
import warnings as _warnings_
from typing import Literal, NamedTuple, Optional, TypedDict, Unpack

try: 
    from ray.rllib.env import ExternalEnv, ExternalMultiAgentEnv
except ModuleNotFoundError as e:
    from ...errors import OptionalModuleNotFoundError
    raise OptionalModuleNotFoundError.suggest(['ray[rllib]']) from e

from ..gymnasium.agent import Agent, AgentManager
from ...callbacks import Callback, CallbackManager
from ...components import Component
from ...errors import TemporaryUnavailableError
from ...refs import Derefable, bounded_deref
from ...systems import BaseSystem


class _EnvHelperMixin(
    ExternalEnv, 
    Component[BaseSystem],
    _abc_.ABC,
):
    r"""
    Helper mixin for :class:`ExternalEnv`s.
    """

    @property
    def system(self):
        r"""Access to the attached system."""
        
        return self.parent

    @_abc_.abstractmethod
    def step_episode(self, episode_id: str, off_policy: bool = False) -> None:
        r"""
        (IMPLEMENT) Execute one step of the episode.

        The implementation typically should:
        1. Call :meth:`log_returns` to log the reward.
        2. Depending on the value of `off_policy`:
            * If ``True``, call :meth:`log_action` to _log_ the computed action.
            * If ``False``, call :meth:`get_action` to _obtain_ the next action 
                and _perform_ it.

        :param episode_id: The episode ID.
        :param off_policy: Whether to perform this operation off-policy.
        :throws TemporaryUnavailableError: 
            If the operation is temporarily unavailable.
        """

        ...

    class EpisodeScheduler(Component['_EnvHelperMixin']):
        class ErrorSpec(NamedTuple):
            stage: Literal['begin', 'step', 'end']
            episode_id: str
            error: Exception

            @property
            def message(self):
                return (
                    f'Episode {self.episode_id!r} @ {self.stage!r}: '
                    f'{self.error}'
                )

        class Config(TypedDict):
            begin: Optional[Callback | Derefable[Callback]]
            step: Optional[Callback | Derefable[Callback]]
            end: Optional[Callback | Derefable[Callback]]
            off_policy: Optional[bool]
            errors: Optional[Literal['raise', 'warn'] | Callback]

        def __init__(
            self, 
            episode_id: str | None, 
            config: Config = Config(),
            **config_kwds: Unpack[Config],
        ):
            self.episode_id = episode_id
            self.config = self.Config(config, **config_kwds)

        @_functools_.cached_property
        def events(self):
            res = CallbackManager[
                # TODO typing
                Literal['error'], self.ErrorSpec
            ](slots=['error'])

            error_handler = self.config.get('errors', 'warn')

            match error_handler:
                case 'raise':
                    def error_handler(spec):
                        raise RuntimeError(spec.message) from spec.error
                case 'warn':
                    def error_handler(spec):
                        _warnings_.warn(RuntimeWarning(spec.message))
                case 'ignore' | None:
                    error_handler = None                
                case _:
                    pass

            if error_handler is not None:
                res['error'].on(error_handler)
                    
            return res

        @property
        def system(self):
            return self.parent.parent

        def setup(self):
            def _callback_of(o):
                return bounded_deref(self.system.events, o, bound=Callback)
            
            curr_episode_id = None

            if self.config.get('begin') is not None:
                @_callback_of(self.config['begin']).on
                def _(*args, **kwargs):
                    nonlocal curr_episode_id
                    if curr_episode_id is not None:
                        return
                    try: curr_episode_id = (
                        self.parent.start_episode(
                            self.episode_id
                        )
                    )
                    except Exception as e: self.events['error'](
                        self.ErrorSpec('begin', self.episode_id, e)
                    )

            if self.config.get('step') is not None:
                @_callback_of(self.config['step']).on
                def _(*args, **kwargs):
                    if curr_episode_id is None:
                        return
                    try: self.parent.step_episode(
                        curr_episode_id,
                        off_policy=self.config.get('off_policy', False),
                    )
                    except TemporaryUnavailableError:
                        pass
                    except Exception as e: self.events['error'](
                        self.ErrorSpec('step', curr_episode_id, e)
                    )

            if self.config.get('end') is not None:
                @_callback_of(self.config['end']).on
                def _(*args, **kwargs):
                    nonlocal curr_episode_id
                    if curr_episode_id is None:
                        return
                    try: self.parent.end_episode(curr_episode_id)
                    except Exception as e: self.events['error'](
                        self.ErrorSpec('end', curr_episode_id, e)
                    )
                    else: curr_episode_id = None

            return self
        
        # TODO repeat? cancel? teardown?
        def teardown(self):
            raise NotImplementedError
        
    def schedule_episode(
        self, 
        episode_id: str | None = None,
        **scheduler_kwds: Unpack[EpisodeScheduler.Config],
    ):
        r"""
        Schedule an episode.
        TODO doc

        :param episode_id: The target episode ID.
        :param off_policy: Whether this episode will be off-policy.

        :return: TODO
        """

        return self.EpisodeScheduler(
            episode_id, 
            config={
                'begin': 'begin',
                'step': 'timestep',
                'end': 'end',
                **scheduler_kwds,
            },
        ).attach(self).setup()
    
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

        The loop should not terminate.

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
    Component[BaseSystem], 
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
    
    def log_action(
        self, episode_id, 
        observation=None, action=None,
    ):
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
    
    def _get_latest_observation(self, episode_id):
        try: return self.agent.observation.value 
        except TemporaryUnavailableError as e:
            res = self._get(episode_id).new_observation
            if res is None:
                raise ValueError(
                    f'Last recorded observation unavailable'
                ) from e
            _warnings_.warn(e.warning())
            return res

    def end_episode(self, episode_id, observation=None):
        if observation is None:
            observation = self._get_latest_observation(episode_id)
        return super().end_episode(
            episode_id, 
            observation=observation,
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
    Component[BaseSystem],
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
    
    def _get_latest_observation(self, episode_id):
        try: return self.agents.observations.value
        except TemporaryUnavailableError as e:
            res = self._get(episode_id).new_observation_dict
            if res is None:
                raise ValueError(
                    f'Last recorded observation unavailable'
                ) from e
            _warnings_.warn(e.warning())
            return res

    def end_episode(self, episode_id, observation_dict=None):
        if observation_dict is None:
            observation_dict = self._get_latest_observation(episode_id)
        return super().end_episode(
            episode_id, 
            observation_dict=observation_dict,
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