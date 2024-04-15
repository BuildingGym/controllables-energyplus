r"""
Base

Scope: Basis for a component in a system, simulated or real-world.
"""

import abc as _abc_
import typing as _typing_

from .. import engines as _engines_


class Component(_abc_.ABC):
    _engine: '_engines_.base.Engine'

    def __attach__(self, engine: '_engines_.base.Engine') -> _typing_.Self:       
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


class ComponentManager(_abc_.ABC):
    pass


__all__ = [
    'Component',
    'ComponentManager',
]
