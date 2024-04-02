import abc as _abc_
import typing as _typing_


from ... import base as _base_
from .... import (
    components as _components_,
    engines as _engines_,
    utils as _utils_,
)

from . import spaces as _spaces_

try: 
    import gymnasium as _gymnasium_
    import gymnasium.core
except ImportError as e:
    raise _base_.OptionalImportError(['gymnasium']) from e


ActType = _gymnasium_.core.ActType
ObsType = _gymnasium_.core.ObsType


BaseVariable = _components_.variables.BaseVariable
BaseControlVariable = _components_.variables.BaseControlVariable


class BaseThinEnv(
    _base_.Addon, 
    _abc_.ABC,
):
    class SpaceVariableEnabler(_utils_.mappings.BaseMapper):
        def __init__(self, simulator: _engines_.simulators.Simulator):
            super().__init__()
            self._simulator = simulator

        def __call__(
            self, 
            space: _spaces_.VariableSpace[BaseVariable.Specs],
        ):
            # TODO !!!!!!!!!!!
            self._simulator.variables.on(space.binding)

    def __attach__(self, engine):
        super().__attach__(engine=engine)

        space_var_enabler = _spaces_.SpaceStructureMapper(
            mapper_base=self.SpaceVariableEnabler(
                simulator=self._engine,
            ),
        )

        for space in self.action_space, self.observation_space:
            space_var_enabler(space)

        return self
    
    '''
    @_abc_.abstractproperty
    def action_space(self) -> _gymnasium_.spaces.Space[ActType]:
        raise NotImplementedError
    '''
    action_space: _gymnasium_.spaces.Space[ActType]

    class SpaceControlVariableMapper(_utils_.mappings.BaseMapper):
        def __init__(self, simulator: _engines_.simulators.Simulator):
            super().__init__()
            self._simulator = simulator

        def __call__(
            self, 
            space: _spaces_.VariableSpace[BaseControlVariable.Specs], 
            value: _typing_.Any,
        ):
            # TODO 
            self._simulator.variables[space.binding].value = value
            return value

    def act(self, action: ActType):
        return _spaces_.SpaceStructureMapper(
            mapper_base=self.SpaceControlVariableMapper(
                simulator=self._engine,
            ),
        )(self.action_space, action)
    
    '''
    @_abc_.abstractproperty
    def observation_space(self) -> _gymnasium_.spaces.Space[ObsType]:
        raise NotImplementedError
    '''
    observation_space: _gymnasium_.spaces.Space[ObsType]

    class SpaceVariableMapper(_utils_.mappings.BaseMapper):
        def __init__(self, simulator: _engines_.simulators.Simulator):
            super().__init__()
            self._simulator = simulator
    
        def __call__(
            self, 
            space: _spaces_.VariableSpace[BaseVariable.Specs],
        ):
            # TODO
            import numpy as _numpy_
            return _numpy_.array(
                self._simulator.variables[space.binding].value,
                dtype=space.dtype,
            ).reshape(space.shape)
            
    def observe(self) -> ObsType:        
        return _spaces_.SpaceStructureMapper(
            mapper_base=self.SpaceVariableMapper(
                simulator=self._engine
            ),
        )(self.observation_space)


__all__ = [
    BaseThinEnv,
]