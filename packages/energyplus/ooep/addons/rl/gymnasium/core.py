import abc as _abc_
import typing as _typing_
import functools as _functools_

# TODO
from . import utils as _utils_
from . import spaces as _spaces_

from ... import base as _base_
from ....specs.components import BaseComponent
from ....specs.systems import BaseSystem
from ....specs.variables import (
    BaseVariable,
    BaseMutableVariable,
)

try: 
    import gymnasium as _gymnasium_
    from gymnasium.core import (
        ActType,
        ObsType,
    )
    import numpy as _numpy_
except ImportError as e:
    raise _base_.OptionalImportError.suggest(['gymnasium', 'numpy']) from e

# TODO
from ....specs.variables import BaseVariable



class SpaceVariable(
    BaseVariable, 
    BaseComponent[BaseSystem],
    #_base_.Addon,
):
    r"""
    TODO
    """

    def __attach__(self, engine):
        super().__attach__(engine)
        # TODO
        self._variables = self._manager.variables
        return self
    
    @property
    def value(self):
        def apply_single(space: _spaces_.VariableSpace):
            def _f_get(ref):
                return self._variables[ref].value
            return _numpy_.array(
                _utils_.StructureMapper(_f_get)(space.binding),
                dtype=space.dtype,
            ).reshape(space.shape)
        
        return _spaces_.SpaceStructureMapper(apply_single)(self.ref)


class MutableSpaceVariable(SpaceVariable):
    r"""
    TODO
    """

    @SpaceVariable.value.setter
    def value(self, data):
        # TODO
        def apply_single(
            # TODO
            space: _spaces_.VariableSpace,#[BaseMutableVariable.Ref], 
            vals: _typing_.Any,
        ):
            def _f_set(ref, val):
                self._variables[ref].value = val
                return val
            return _utils_.StructureMapper(_f_set)(space.binding, vals)

        return _spaces_.SpaceStructureMapper(apply_single)(self.ref, data)



class BaseSpaceVariableContainer(
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

    .. note::
        This class cannot be used as a `gymnasium.Env` alone; 
        rather, it's designed to be integrated with 
        a Gymnasium-compliant environment (e.g. `gymnasium.Env`) 
        as a "mixin" to ensure compatibility with EnergyPlus OOEP engines.

    .. seealso::
        * `gymnasium.spaces.Space <https://gymnasium.farama.org/api/spaces/#gymnasium.spaces.Space>`_
        * `gymnasium.Env.action_space <https://gymnasium.farama.org/api/env/#gymnasium.Env.action_space>`_
        * `gymnasium.Env.observation_space <https://gymnasium.farama.org/api/env/#gymnasium.Env.observation_space>`_
    """

    action_space: _gymnasium_.spaces.Space[ActType]
    r"""All possible actions within the environment"""
    observation_space: _gymnasium_.spaces.Space[ObsType]
    r"""All possible observations or states the environment can be in."""

    @_functools_.cached_property
    def action(self):
        r"""TODO"""
        return MutableSpaceVariable(self.action_space)

    @_functools_.cached_property
    def observation(self):
        r"""TODO"""
        return SpaceVariable(self.observation_space)

    def __attach__(self, engine):
        super().__attach__(engine)

        self.action.__attach__(self._manager)
        self.observation.__attach__(self._manager)

        return self

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


import dataclasses as _dataclasses_

@_dataclasses_.dataclass
class SpaceVariableContainer(BaseSpaceVariableContainer):
    r"""
    Standalone class for interfacing between 
    simulation engines and `Gymnasium spaces <https://gymnasium.farama.org/api/spaces/>`_.

    This is an implementation example of its base class :class:`BaseVariableSpaceContainer`.
    """

    action_space: _gymnasium_.spaces.Space[ActType]
    observation_space: _gymnasium_.spaces.Space[ObsType]


__all__ = [
    'ActType',
    'ObsType',
    'SpaceVariable',
    'MutableSpaceVariable',
    'BaseSpaceVariableContainer',
    'SpaceVariableContainer',
]
