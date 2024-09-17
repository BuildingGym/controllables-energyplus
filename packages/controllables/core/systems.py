r"""
Specs for systems.
"""


import abc as _abc_
from typing import Self, Literal

from .components import BaseComponent
from .variables import BaseVariable, BaseVariableManager
from .callbacks import Callback, CallbackManager


class BaseSystem(_abc_.ABC):
    r"""
    System base class.

    A system is a group of components.
    """

    # TODO
    @_abc_.abstractmethod
    def start(self) -> Self:
        r"""
        Start the system.
        
        :return: This system.
        :raises RuntimeError: If the system is already started.
        """

        ...

    started: bool
    r"""Whether the system is started."""

    @_abc_.abstractmethod
    def wait(self, timeout: float | None = None) -> Self:
        r"""
        Wait for the system to finish.
        TODO Returns immediately if the system is not started.

        :param timeout:
            The maximum time to wait for the system to finish.
            If :class:`None`, waits indefinitely..
        :raises TimeoutError: If the system does not finish in time.
        :return: This system.
        """

        ...

    # TODO __await__?

    @_abc_.abstractmethod
    def stop(self, timeout: float | None = None) -> Self:
        r"""
        Stop the system.

        :param timeout: 
            The maximum time to wait for the system to stop.
            If :class:`None`, waits indefinitely. (TODO)
        :raises TimeoutError: If the system does not stop in time.
        :raises RuntimeError: If the system is not started.
        :return: This system.
        """

        ...

    variables: BaseVariableManager[Literal['time'], BaseVariable]
    r"""
    Root variable manager.

    TODO doc builtin vars (e.g. 'time')
    """

    events: CallbackManager[Literal['begin', 'step', 'end'], Callback]
    r"""
    Root event manager.

    TODO doc builtin events (e.g. 'begin', 'step', 'end')
    """

    # ############
    # TODO deprecate
    def run(self) -> Self:
        raise DeprecationWarning('Deprecated!!! use `start` instead')

    @property
    def awaitable(self):
        raise DeprecationWarning('Deprecated!!! use `start` directly')
    

class SystemShortcutMixin(BaseSystem):
    r"""
    Opt-in mixin for :class:`BaseSystem` shortcuts.
    Useful for user-facing classes and the impatient.
    """

    def add(self, component: BaseComponent[Self]):
        r"""
        Add a component to this system.
        Shortcut for :meth:`BaseComponent.__attach__`.

        :param component: The component to add.
        """

        component.__attach__(self)
        return self
    
    def remove(self, component: BaseComponent[Self]):
        r"""
        Remove a component from this system.
        Shortcut for :meth:`BaseComponent.__detach__`.

        :param component: The component to remove.
        """

        component.__detach__(self)
        return self
    
    def on(self, event_ref, listener=None):
        r"""
        Register an event listener.
        Shortcut for `self.events.on`.

        :param event_ref: The event reference.
        :param listener: The event listener;
            If `None`, returns a `on` function/decorator for the event.
        """

        if listener is None:
            def _decorator(listener):
                self.events.on(event_ref, listener)
                return listener
            return _decorator

        self.events.on(event_ref, listener)
        return self
    
    def off(self, event_ref, listener=None):
        r"""
        Unregister an event listener.
        Shortcut for `self.events.off`.

        :param event_ref: The event reference.
        :param listener: The event listener;
            If `None`, returns a `off` function/decorator for the event.
        """

        if listener is None:
            def _decorator(listener):
                self.events.off(event_ref, listener)
                return listener
            return _decorator

        self.events.off(event_ref, listener)
        return self
    
    def __getitem__(self, var_ref):
        r"""
        Get a variable by reference.
        Shortcut for `self.variables.__getitem__`.

        .. seealso:: :meth:`VariableManager.__getitem__`
        """

        # TODO
        return self.variables.__getitem__(var_ref)
    
    def __delitem__(self, var_ref):
        r"""
        Delete a variable by reference.
        Shortcut for `self.variables.__delitem__`.

        .. seealso:: :meth:`VariableManager.__delitem__`
        """

        self.variables.__delitem__(var_ref)


__all__ = [
    'BaseSystem',
    'SystemShortcutMixin',
]