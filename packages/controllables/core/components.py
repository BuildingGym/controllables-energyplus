r"""
TODO

Scope: Abstract classes for component and component managers.
"""

import abc as _abc_
import typing as _typing_
import functools as _functools_ 

#from . import workflows as _workflows_


class BaseComponentManager(_abc_.ABC):
    pass

_BaseComponentManagerT = _typing_.TypeVar(
    '_BaseComponentManagerT', 
    #bound=BaseComponentManager,
)

# TODO multiple managers
# TODO multi class component manager
class BaseComponent(
    _abc_.ABC, 
    _typing_.Generic[_BaseComponentManagerT],
):
    r"""
    TODO
    """

    '''
    # TODO !!!!!!!!!!!!!!!!!!!
    class Workflow(_abc_.ABC):
        def __init__(
            self, 
            ref: _typing_.Any | None = None, 
            target: 'BaseComponent.WorkflowManager | None' = None,
        ):
            self.ref = ref
            self.target = target

    class WorkflowManager(
        _utils_.callbacks.CallbackManager[
            _typing_.Literal['attach', 'detach'],
            _utils_.callbacks.Callback[
                [Workflow], _typing_.Any,
            ],
        ], 
        _abc_.ABC,
    ):
        pass

    # TODO solve conflict!!!!!!!!
    @_functools_.cached_property
    def _TODO_workflows(self):
        return self.WorkflowManager()
    # TODO
    '''

    __manager__: _BaseComponentManagerT | None = None
    @property
    def _manager(self) -> _BaseComponentManagerT:
        return self.__manager__
    
    @_functools_.cached_property
    def __manager_callbacks__(self):
        from .callbacks import CallbackManager

        callbacks = CallbackManager()

        @callbacks['attach'].use
        def _(manager: _BaseComponentManagerT):
            if getattr(self, '__manager__', None) is not None:
                if manager == self.__manager__:
                    return self
                raise ValueError(
                    f'Component already has manager attached: {self.__manager__}'
                )
            
            setattr(self, '__manager__', manager)

        @callbacks['detach'].use
        def _(manager: _BaseComponentManagerT):
            raise NotImplementedError
            if self.__engine is None:
                raise ValueError('Component does not have Engine attached.')
            self.__engine = None

        return callbacks
        

    # TODO !!!!!!
    #@_workflows_.observable
    def __attach__(self, manager: _BaseComponentManagerT) -> _typing_.Self:
        if getattr(self, '__manager__', None) is not None:
            if manager == self.__manager__:
                return self
            raise ValueError(
                f'Component already has manager attached: {self.__manager__}'
            )
        
        setattr(self, '__manager__', manager)

        # TODO
        '''
        self._TODO_workflows.emit(
            'attach',
            self.Workflow(
                ref='attach', target=self,
            ),
        )
        '''

        return self
    
    #@_workflows_.observable
    def __detach__(self, manager: _BaseComponentManagerT) -> _typing_.Self:
        raise NotImplementedError
        if self.__engine is None:
            raise ValueError('Component does not have Engine attached.')
        self.__engine = None
        return self


__all__ = [ 
    'BaseComponent',
    'BaseComponentManager',
]
