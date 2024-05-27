r"""
Base

Scope: Abstract components and managers.
"""

import abc as _abc_
import typing as _typing_


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
    _engine: ComponentManagerType

    def __attach__(self, engine: ComponentManagerType) -> _typing_.Self:       
        if getattr(self, '_engine', None) is not None:
            if engine == self._engine:
                return self            
            raise ValueError('Component already has Engine attached.')
        
        setattr(self, '_engine', engine)

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
    'Component',
    'ComponentManager',
]
