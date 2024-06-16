import abc as _abc_
import typing as _typing_


# TODO
from . import utils as _utils_

from ... import base as _base_
from .... import (
    components as _components_,
)

from . import spaces as _spaces_

try: 
    import gymnasium as _gymnasium_
    import gymnasium.core
    import numpy as _numpy_
except ImportError as e:
    raise _base_.OptionalImportError.suggest(['gymnasium', 'numpy']) from e


ActType = _gymnasium_.core.ActType
ObsType = _gymnasium_.core.ObsType


BaseVariable = _components_.variables.BaseVariable
BaseMutableVariable = _components_.variables.BaseMutableVariable



# TODO
class VariableSpaceView(_base_.Addon):
    r"""
    A view of a variable space within an engine.
    """

    # TODO typing
    def __init__(self, space: _spaces_.VariableSpace[BaseVariable.Ref]):
        super().__init__()
        self._space = space
        # TODO
        #self._variables = _components_.variables.VariableManager()

    def __attach__(self, engine):
        super().__attach__(engine)
        # TODO
        self._variables = self._engine.variables
        #self._variables.__attach__(engine=engine)
        return self

    def on(self):
        def apply_single(space: _spaces_.VariableSpace):
            nonlocal self
            # TODO
            self._variables.on(space.binding)

        # TODO ret ??
        _spaces_.SpaceStructureMapper(apply_single)(self._space)
        
    def off(self):
        # TODO
        raise NotImplementedError
    
    @property
    def value(self):
        def apply_single(space: _spaces_.VariableSpace):
            nonlocal self
            return _numpy_.array(
                self._variables[space.binding].value,
                dtype=space.dtype,
            ).reshape(space.shape)
        
        return _spaces_.SpaceStructureMapper(apply_single)(self._space)


class MutableVariableSpaceView(VariableSpaceView):
    r"""
    A view of a mutable variable space within an engine.
    """

    @VariableSpaceView.value.setter
    def value(self, data):
        # TODO
        def apply_single(space: _spaces_.VariableSpace[BaseMutableVariable.Ref], o: _typing_.Any):
            nonlocal self
            self._variables[space.binding].value = o
            return o
        
        return _spaces_.SpaceStructureMapper(apply_single)(self._space, data)


import functools as _functools_


class BaseThinEnv(_base_.Addon, _abc_.ABC):
    r"""
    Minimal abstract class for interfacing between 
    simulation engines and `Gymnasium spaces <https://gymnasium.farama.org/api/spaces/>`_. 

    :ivar action_space: 
        All possible actions within the environment.     
    :ivar observation_space: 
        All possible observations or states the environment can be in.

    Fundamental elements of the above spaces can only be 
    associated with regular variables (TODO link),
    i.e. variables with `value` readable.

    .. note::
        This class cannot be used as a `gymnasium.Env` alone; 
        rather, it's designed to be integrated with 
        a Gymnasium-compliant environment (e.g. `gymnasium.Env`) 
        as a "mixin" to ensure compatibility with EnergyPlus OOEP engines.

        Inherited classes must have `action_space` and `observation_space` defined.
        Any `fundamental space <https://gymnasium.farama.org/api/spaces/fundamental/#fundamental-spaces>`_
        must be associated with a variable reference (TODO link) from an engine.

    .. seealso::
        * `gymnasium.Env.action_space <https://gymnasium.farama.org/api/env/#gymnasium.Env.action_space>`_
        * `gymnasium.Env.observation_space <https://gymnasium.farama.org/api/env/#gymnasium.Env.observation_space>`_
    """

    action_space: _gymnasium_.spaces.Space[ActType]
    observation_space: _gymnasium_.spaces.Space[ObsType]

    @_functools_.cached_property
    def _action_view(self):
        return MutableVariableSpaceView(self.action_space)
    
    @_functools_.cached_property
    def _observation_view(self):
        return VariableSpaceView(self.observation_space)

    def __attach__(self, engine):
        super().__attach__(engine)

        self._action_view.__attach__(self._engine)
        self._observation_view.__attach__(self._engine)

        for view in self._action_view, self._observation_view:
            view.on()

        return self

    def act(self, action: ActType):
        r"""Submit an action to the attached engine.
        
        :param action: An action within the action space :attr:`action_space`.
        :return: The action seen by the enviornment. Identical to the `action` submitted.
        """
        self._action_view.value = action
        return action

    def observe(self) -> ObsType:
        r"""Obtain an observation from the attached engine.
        
        :return: An observation from the observation space :attr:`observation_space`.
        """
        return self._observation_view.value


import dataclasses as _dataclasses_

@_dataclasses_.dataclass
class ThinEnv(BaseThinEnv):
    r"""
    Standalone class for interfacing between 
    simulation engines and `Gymnasium spaces <https://gymnasium.farama.org/api/spaces/>`_.

    This is an implementation example of its base class `BaseThinEnv`.
    """

    action_space: _gymnasium_.spaces.Space[ActType]
    observation_space: _gymnasium_.spaces.Space[ObsType]


__all__ = [
    'BaseThinEnv',
    'ThinEnv',
]