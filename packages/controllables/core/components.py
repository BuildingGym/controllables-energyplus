r"""
TODO

Scope: Abstract classes for component and component managers.
"""


import abc as _abc_
from typing import Any, Generic, Self, TypeVar, TypeAlias


ComponentParentT = TypeVar('ComponentParentT')


class BaseComponent(
    _abc_.ABC,
    Generic[ComponentParentT],
):
    @property
    def parent(self) -> ComponentParentT:
        r"""
        The parent of this component.

        :raises ValueError: If the component does not have a parent attached.
        """

        ...

    @_abc_.abstractmethod
    def __attach__(self, parent: ComponentParentT) -> Any:
        r"""
        Attach this component to a parent.

        :param parent: The parent to attach to.
        """

        ...

    @_abc_.abstractmethod
    def __detach__(self, parent: ComponentParentT | None = None) -> Any:
        r"""
        Detach this component from a parent.

        :param parent: The parent to detach from, optional.
        """

        ...


# TODO multiple managers
# TODO multi class component manager
class Component(
    BaseComponent[ComponentParentT], 
    Generic[ComponentParentT],
):
    r"""
    TODO
    """

    __parent__: ComponentParentT | None = None

    @property
    def parent(self):
        if self.__parent__ is None:
            raise ValueError('Component does not have a parent attached')
        return self.__parent__
    
    # TODO !!!
    #@_contextlib_.contextmanager
    def _TODO_attach(self, parent):
        return ...

    def __attach__(self, parent):
        if self.__parent__ is not None:
            if parent == self.__parent__:
                return self
            raise ValueError(
                f'Component already has a parent attached: {self.__parent__}'
            )
        
        self.__parent__ = parent
    
    # TODO __detach__ when __del__!!!!
    def __detach__(self, parent=None):
        if self.__parent__ is None:
            raise ValueError('Component does not have a parent attached.')
        self.__parent__ = None

    def attach(self, parent) -> Self:
        self.__attach__(parent)
        return self
    
    def detach(self, parent=None) -> Self:
        self.__detach__(parent)
        return self
    

__all__ = [ 
    'Component',
]


import contextlib as _contextlib_
import functools as _functools_


ComponentParentT: TypeAlias = TypeVar('ComponentParentT')


class TODONext_ProtoComponent(_abc_.ABC, Generic[ComponentParentT]):
    @_abc_.abstractmethod
    def attach_to(self, parent: ComponentParentT) -> \
        _contextlib_.AbstractContextManager \
        | _contextlib_.AbstractAsyncContextManager:
        ...

ComponentT = TypeVar('ComponentT', bound=TODONext_ProtoComponent)

class TODONext_ProtoComponentManager(_abc_.ABC, Generic[ComponentT]):
    @_abc_.abstractmethod
    def attach(self, component: TODONext_ProtoComponent) -> Self:
        ...
    

class TODONext_ComponentManager(TODONext_ProtoComponentManager):
    @_functools_.cached_property
    def _attachments(self):
        return _contextlib_.ExitStack()

    def attach(self, component):
        self._attachments.enter_context(component.attach_to(self))
        return self


# TODO
__all__