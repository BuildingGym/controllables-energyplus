r"""
Systems.

"And-God-said"s, "Let-there-be"s. (Genesis 1)
"""


import abc as _abc_
import functools as _functools_
from typing import Generic, Self, Literal, Mapping, TypeVar

from .components import Component
from .refs import RefT, ProtoRefManager
from .variables import BaseVariable, BaseVariableManager, VariableManager, ValT
from .callbacks import BaseCallback, BaseCallbackManager, Callback, CallbackManager


# TODO mv
from typing import Callable, Self

class ProtoObservable(_abc_.ABC):
    # TODO mv callbacks
    events: BaseCallbackManager


class ObservableOpsMixin(ProtoObservable):
    r"""
    TODO
    """
    
    def on(self, event_ref, listener: Callable | None = None) -> Self:
        r"""
        Register an event listener.
        Shortcut for `self.events.on`.

        :param event_ref: The event reference.
        :param listener: The event listener.
        :return: 
        * If ``listener`` is ``None``, an `on` function/decorator for the event.
        * Otherwise, this system.
        """

        if listener is None:
            def _decorator(listener):
                self.events.on(event_ref, listener)
                return listener
            return _decorator

        self.events.on(event_ref, listener)
        return self
    
    def off(self, event_ref, listener: Callable | None = None) -> Self:
        r"""
        Unregister an event listener.
        Shortcut for `self.events.off`.

        :param event_ref: The event reference.
        :param listener: The event listener.
        :return: 
        * If `listener` is ``None``, an `off` function/decorator for the event.
        * Otherwise, this system.
        """

        if listener is None:
            def _decorator(listener):
                self.events.off(event_ref, listener)
                return listener
            return _decorator

        self.events.off(event_ref, listener)
        return self
    

# TODO mv
class ProtoProcess(_abc_.ABC):
    r"""
    Process protocol class.
    """

    @_abc_.abstractmethod
    def start(self) -> Self:
        r"""
        (IMPLEMENT) Start the process and return _immediately_.
        
        :return: This process.
        :raises RuntimeError: If the process is already started.
        """

        ...

    @_abc_.abstractmethod
    def wait(self, timeout: float | None = None) -> Self:
        r"""
        (IMPLEMENT) Wait for the process to finish.
        Returns immediately if the process is not started.

        :param timeout:
            The maximum time (seconds) to wait for the process to finish.
            If ```None```, waits indefinitely.
        :raises TimeoutError: If the process does not finish in time.
        :return: This process.
        """

        ...

    # TODO __await__?

    @_abc_.abstractmethod
    def stop(self) -> Self:
        r"""
        (IMPLEMENT) Stop the process and return _immediately_.

        :raises RuntimeError: If the process is not started.
        :return: This process.
        """

        ...


class ProtoObservableProcess(ProtoObservable, ProtoProcess):
    r"""
    Observable process protocol class.
    """

    events: BaseCallbackManager[Literal['begin', 'step', 'end'], BaseCallback]
    r"""
    (IMPLEMENT) Root event manager.

    Implementaions may, optionally, provide these builtin events:

    * `'begin'`: Emitted when the process starts.
    * `'step'`: Emitted at each step (e.g. timestep, clock tick) of the process.
    * `'end'`: Emitted when the process ends.
    """

    variables: BaseVariableManager[Literal['running', 'time'], BaseVariable]
    r"""
    (IMPLEMENT) Root variable manager.

    Implementaions may, optionally, provide these builtin variables:

    * `'running'`: Whether the process is running.
    * `'time'`: The current time inside the process.
    """


class SimpleProcess(
    ProtoObservableProcess,
    #ProtoRefManager[RefT, VarT],
    _abc_.ABC,
):
    r"""
    Simple process class.

    This class may be used to represent a typical
    `Markov decision process <https://wikipedia.org/wiki/markov_decision_process>`_.
    """

    # TODO 
    def __init__(self, variables=None, slots=[]): 
        super().__init__()
        self.variables = VariableManager(
            variables, 
            slots=('running', 'time', *slots),
        )

    @_functools_.cached_property
    def events(self):
        return CallbackManager(slots=('begin', 'timestep', 'end'))

    def start(self):
        if self.variables['running'].value:
            raise RuntimeError('Process is already running')
        
        self.variables['running'].value = True
        self.events['begin']()

        return self

    def step(self, state: Mapping[RefT, ValT], /, **state_kwds) -> Self:
        r"""
        TODO
        """

        if not self.variables['running'].value:
            raise RuntimeError(f'Process is not started yet. Call {self.start!r}')
        
        state = dict(state, **state_kwds)
        for ref, val in state.items():
            self.variables[ref].value = val
        self.events['timestep']()

        return self
    
    def wait(self, timeout=None):
        self.variables['running'].when(False).wait(timeout=timeout)
        return self
    
    def stop(self):
        if not self.variables['running'].value:
            raise RuntimeError('Process is not running')
        
        self.events['end']()
        self.variables['running'].value = False

        return self
    

# TODO
class ProtoPersistentProcess(ProtoProcess):
    pass



# TODO rm?
class BaseSystem(_abc_.ABC):
    r"""
    System base class.

    This class may be used to implement a 
    `discrete-event <https://wikipedia.org/wiki/discrete-event_simulation>`_
    control interface.

    .. seealso:: https://wikipedia.org/wiki/dynamical_system
    """

    @_abc_.abstractmethod
    def start(self) -> Self:
        r"""
        (IMPLEMENT) Start the system and return _immediately_.
        
        :return: This system.
        :raises RuntimeError: If the system is already started.
        """

        ...

    started: bool
    r"""(IMPLEMENT) Whether the system is started."""

    @_abc_.abstractmethod
    def wait(self, timeout: float | None = None) -> Self:
        r"""
        (IMPLEMENT) Wait for the system to finish.
        Returns immediately if the system is not started.

        :param timeout:
            The maximum time (seconds) to wait for the system to finish.
            If ```None```, waits indefinitely..
        :raises TimeoutError: If the system does not finish in time.
        :return: This system.
        """

        ...

    # TODO __await__?

    @_abc_.abstractmethod
    def stop(self) -> Self:
        r"""
        (IMPLEMENT) Stop the system and return _immediately_.

        :raises RuntimeError: If the system is not started.
        :return: This system.
        """

        ...

    variables: BaseVariableManager[Literal['running', 'time'], BaseVariable]
    r"""
    (IMPLEMENT) Root variable manager.

    Implementaions may, optionally, provide these builtin variables:

    * `'running'`: Whether the system is running.
    * `'time'`: The current time inside the system.
    """

    events: CallbackManager[Literal['begin', 'timestep', 'end'], Callback]
    r"""
    (IMPLEMENT) Root event manager.

    Implementaions may, optionally, provide these builtin events:

    * `'begin'`: Emitted when the system starts.
    * `'timestep'`: Emitted at each timestep (clock tick) of the system.
    * `'end'`: Emitted when the system ends.
    """

    def add(self, component: Component[Self]):
        r"""
        Add a component to this system.
        Shortcut for :meth:`BaseComponent.__attach__`.

        :param component: The component to add.
        :return: This system.
        """

        component.__attach__(self)
        return self
    
    def remove(self, component: Component[Self]):
        r"""
        Remove a component from this system.
        Shortcut for :meth:`BaseComponent.__detach__`.

        :param component: The component to remove.
        :return: This system.
        """

        component.__detach__(self)
        return self
    
    def on(self, event_ref, listener=None):
        r"""
        Register an event listener.
        Shortcut for `self.events.on`.

        :param event_ref: The event reference.
        :param listener: The event listener.
        :return: 
        * If ``listener`` is ``None``, an `on` function/decorator for the event.
        * Otherwise, this system.
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
        :param listener: The event listener.
        :return: 
        * If `listener` is ``None``, an `off` function/decorator for the event.
        * Otherwise, this system.
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

    def __contains__(self, var_ref):
        # TODO
        return self.variables.__contains__(var_ref)


__all__ = [
    'BaseSystem',
]