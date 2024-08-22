r"""
Systems.
"""


import abc as _abc_
import functools as _functools_
import asyncio as _asyncio_

from typing import Self, Literal

from .. import utils as _utils_

from .workflows import WorkflowManager
from .components import BaseComponent
from .variables import BaseVariableManager
from .callbacks import CallbackManager


class BaseSystem(_abc_.ABC):
    r"""
    System base class.

    A system is a collection of components 
    that work together to achieve a goal.
    """

    WorkflowManager = WorkflowManager[
        Literal[
            'run:pre', 
            'run:post', 
            'stop:pre', 
            'stop:post',
        ], 
        Self,
    ]
    r"""
    Workflow manager class.
    
    Implementations shall, at minimum, emit the following workflows:
    * `run:pre`: emitted before running the system.
    * `run:post`: emitted after running the system.
    * `stop:pre`: emitted before stopping the system.
    * `stop:post`: emitted after stopping the system.

    Override this attribute to add custom workflows.
    """

    @_functools_.cached_property
    def workflows(self) -> WorkflowManager:
        r"""
        Workflows for the system.

        :return: The workflow manager.
        """

        return WorkflowManager().__attach__(self)

    @_abc_.abstractmethod
    def run(self) -> Self:
        r"""
        Run the system.
        
        :return: This system.
        :raises RuntimeError: If the system is already running.
        """

        ...

    @_abc_.abstractmethod
    def stop(self, timeout: float | None = None) -> Self:
        r"""
        Stop the system.

        :param timeout: 
            The maximum time to wait for the system to stop.
            If :class:`None`, waits indefinitely;
            Otherwise, raises a :class:`TimeoutError` 
            if the system does not stop in time. (TODO)
        :return: This system.
        :raises RuntimeError: If the system is not running.
        """

        ...

    variables: BaseVariableManager
    r"""Root variable manager."""

    events: CallbackManager
    r"""Root event manager."""

    class AsyncOps(BaseComponent['BaseSystem']):
        r"""
        Asynchronous operations for the system.
        """

        def __init__(self, loop: _asyncio_.AbstractEventLoop = None):
            self.__asyncify__ = _utils_.awaitables.asyncify(loop=loop)

        def run(self, *args, **kwargs):
            r"""
            Run the system asynchronously.
            """

            return _asyncio_.create_task(
                self.__asyncify__(self._manager.run)
                (*args, **kwargs)
            )

        def stop(self, *args, **kwargs):
            r"""
            Stop the system asynchronously.
            """

            return _asyncio_.create_task(
                self.__asyncify__(self._manager.stop)
                (*args, **kwargs)
            )
        
    @_functools_.cached_property
    def awaitable(self):
        r"""
        Asynchronous interface.
        """

        return self.AsyncOps().__attach__(self)
    

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