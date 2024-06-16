r"""
Base

Scope: Abstract components and managers.
"""

import abc as _abc_
import typing as _typing_
import functools as _functools_ 

from .. import utils as _utils_

# TODO
class ComponentWorkflow(_utils_.events.Event['Component']):
    pass

class ComponentWorkflowManager(
    _utils_.events.EventManager, 
):
    # TODO
    def keys(self):
        return [
            'attach',
            #'detach',
        ]
    
    def emit(self, ref: ComponentWorkflow.Ref, event: ComponentWorkflow):
        return super().emit(ref, event)

class ComponentManager(_abc_.ABC):
    pass

ComponentManagerType = _typing_.TypeVar(
    'ComponentManagerType', 
    bound=ComponentManager,
)

class Component(
    _abc_.ABC, 
    _typing_.Generic[ComponentManagerType],
):
    @_functools_.cached_property
    def _workflows(self):
        return ComponentWorkflowManager()
    
    _engine: ComponentManagerType

    def __attach__(self, engine: ComponentManagerType) -> _typing_.Self:
        if getattr(self, '_engine', None) is not None:
            if engine == self._engine:
                return self
            raise ValueError(
                f'Component already has Engine attached. '
                f'{engine} conflicts with {self._engine}.'
            )
        
        setattr(self, '_engine', engine)
        self._workflows.emit(
            'attach',
            ComponentWorkflow(
                ref='attach', target=self,
            ),
        )

        return self
    
    '''
    # TODO @contextlib.contextmanager instead???
    def __detach__(self, engine: '_engines_.base.Engine') -> _typing_.Self:
        if self.__engine is None:
            raise ValueError('Component does not have Engine attached.')
        self.__engine = None
        return self
    '''



__all__ = [
    'ComponentWorkflow',
    'ComponentWorkflowManager',    
    'Component',
    'ComponentManager',
    'ComponentManagerType',
]
