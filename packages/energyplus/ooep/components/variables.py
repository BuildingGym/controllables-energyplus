r"""
Variables.

Scope: Variable management for engines and worlds.
"""

import abc as _abc_
import typing as _typing_
import functools as _functools_
import dataclasses as _dataclasses_
import itertools as _itertools_
import contextlib as _contextlib_

from . import (
    base as _base_,
    worlds as _worlds_,
)

from .. import (
    exceptions as _exceptions_,
    utils as _utils_,
)


# TODO naming!!!!!!!!!!!!!!!!
class BaseVariable(_base_.Component, _abc_.ABC):
    r"""Variable base class."""

    class Ref(_abc_.ABC):
        @_abc_.abstractmethod
        def __build__(self) -> 'BaseVariable':
            r"""Reconstructs an object from this reference."""
            raise NotImplementedError

    def __init__(self, ref: Ref):
        super().__init__()
        self._ref = ref

    @property
    def ref(self) -> Ref:
        r"""Get the reference to this variable."""
        return self._ref

    @property
    @_abc_.abstractmethod
    def value(self):
        r"""
        Get the value of this variable.

        :return: The value of this variable.
        """
        raise NotImplementedError

class BaseMutableVariable(BaseVariable, _abc_.ABC):
    r"""Mutable variable base class."""

    @BaseVariable.value.setter
    @_abc_.abstractmethod
    def value(self, o: _typing_.Any):
        r"""
        Set the value of this variable.

        :param o: The value to set.
        """
        raise NotImplementedError

# TODO 
class BaseVariableManager(_base_.Component, _abc_.ABC):
    r"""Variable manager base class.

    """

    @_abc_.abstractmethod
    def on(self, ref: str | BaseVariable.Ref) -> _typing_.Self:
        r"""
        Turn on a variable by reference.
        Implementation shall enable access to the variable 
        via the :meth:`__getitem__` method.

        :param ref: 
            Reference to the variable to be enabled.
            This can be a string or a reference object.
            Strings shall be used as "symbols" for 
            predefined shortcut variables.
        :return: This variable manager instance.
        """
        raise NotImplementedError
    
    @_abc_.abstractmethod
    def off(self, ref: str | BaseVariable.Ref) -> _typing_.Self:
        r"""
        Turn off a variable by reference.
        Implementation shall remove access to the variable 
        via the :meth:`__getitem__` method,
        and release any resources associated with the variable, 
        if necessary.

        :param ref: See :meth:`on`.
        :return: This variable manager instance.
        """
        raise NotImplementedError

    @_abc_.abstractmethod
    def __getitem__(self, ref: str | BaseVariable.Ref) -> BaseVariable:
        r"""
        Access a variable by its reference.

        :param ref: Reference to the variable to be accessed.
        :return: Variable associated with reference `ref`.

        .. seealso:: :meth:`on`
        """
        raise NotImplementedError


class CoreExceptionableMixin(_base_.Component):
    r"""
    Exception handling mixin for core API calls.
    """

    @_contextlib_.contextmanager
    def _ensure_exception(self):
        r"""
        Ensure that core API exceptions are caught and relevant errors raised.

        :raises: :class:`TemporaryUnavailableError` if an error has occurred.

        .. seealso:: https://energyplus.readthedocs.io/en/latest/datatransfer.html#datatransfer.DataExchange.api_error_flag
        """
        try:
            yield
        finally:
            api = self._engine._core.api
            state = self._engine._core.state
            if api.exchange.api_error_flag(state):
                api.exchange.reset_api_error_flag(state)
                raise _exceptions_.TemporaryUnavailableError(
                    'Core API data exchange error.'
                )


import datetime as _datetime_

class WallClock(
    BaseVariable,
    _base_.Component,
):
    r"""Wall clock variable class."""

    @_dataclasses_.dataclass(frozen=True)
    class Ref(BaseVariable.Ref):
        r"""
        Reference to a wall clock.
        
        :param calendar: 
            Whether to use the calendar year or the simulation year.
            If `True`, this reference refers to a calendar wall clock.
            .. seealso::
                * https://github.com/NREL/EnergyPlus/issues/10210
        """

        calendar: bool = False

        def __build__(self):
            return WallClock(ref=self)

    ref: Ref

    @property
    def value(self):
        api = self._engine._core.api.exchange
        state = self._engine._core.state
        try:
            return _datetime_.datetime(
                year=(
                    api.calendar_year(state) 
                    if self.ref.calendar else 
                    api.year(state)
                ),
                month=api.month(state),
                day=api.day_of_month(state),
                hour=api.hour(state),
                # NOTE core api returns 1-60: datetime requires range(60)
                minute=api.minutes(state) - 1,
                # TODO
                tzinfo=_datetime_.timezone(offset=_datetime_.timedelta(0)),
            )
        except ValueError:
            # TODO better handling!!!!!!!!!!!!!
            # TODO err flag temp unavailable!!!!!!!!!!!
            raise _exceptions_.TemporaryUnavailableError()



class Actuator(
    BaseMutableVariable,
    CoreExceptionableMixin,
    _base_.Component,
):
    r"""
    Actuator variable class.

    .. note:: DO NOT instantiate this class directly. 
        Use the :class:`VariableManager` instead.
    """

    @_dataclasses_.dataclass(frozen=True)
    class Ref(BaseMutableVariable.Ref):
        r"""
        Reference to an actuator.

        :param type: The type of the actuator.
        :param control_type: The control type of the actuator.
        :param key: The key of the actuator.

        Example usage:

        .. code-block:: python        
            Actuator.Ref(
                type='Weather Data', 
                control_type='Outdoor Dew Point', 
                key='Environment',
            )

        .. seealso:: TODO link
        """

        type: str
        control_type: str
        key: str

        def __build__(self): 
            return Actuator(ref=self)

    ref: Ref

    @property
    def _core_handle(self):
        r"""
        Get the internal handle of the actuator.

        :raises: :class:`TemporaryUnavailableError` if the handle is not available.

        ...seealso:: 
            * https://energyplus.readthedocs.io/en/latest/datatransfer.html#datatransfer.DataExchange.get_actuator_handle
        """
        res = self._engine._core.api.exchange.get_actuator_handle(
            self._engine._core.state,
            component_type=self.ref.type,
            control_type=self.ref.control_type,
            actuator_key=self.ref.key,
        )
        if res == -1:
            raise _exceptions_.TemporaryUnavailableError() 
        return res

    @property
    def value(self):
        r"""
        Get the value of the actuator.

        :raises: :class:`TemporaryUnavailableError` if the value is not available.
        """
        with self._ensure_exception():
            return self._engine._core.api.exchange.get_actuator_value(
                self._engine._core.state,
                actuator_handle=self._core_handle,
            )

    @value.setter
    def value(self, n: float):
        r"""
        Set the value of the actuator.

        :param n: The value to set the actuator to.
        """
        self._engine._core.api.exchange.set_actuator_value(
            self._engine._core.state,
            actuator_handle=self._core_handle,
            actuator_value=float(n),
        )

    def reset(self):
        r"""
        Reset the actuator.
        This transfers the control of the actuator back to attached engine.

        ...seealso:: https://energyplus.readthedocs.io/en/latest/datatransfer.html#datatransfer.DataExchange.reset_actuator
        """
        self._engine._core.api.exchange.reset_actuator(
            self._engine._core.state,
            actuator_handle=self._core_handle,
        )


class InternalVariable(
    BaseVariable,
    CoreExceptionableMixin,
    _base_.Component,
):
    @_dataclasses_.dataclass(frozen=True)
    class Ref(BaseVariable.Ref):
        type: str
        key: str

        def __build__(self):
            return InternalVariable(ref=self)

    ref: Ref

    @property
    def _core_handle(self):
        res = self._engine._core.api.exchange.get_internal_variable_handle(
            self._engine._core.state,
            variable_name=self.ref.type,
            variable_key=self.ref.key
        )
        if res == -1:
            raise _exceptions_.TemporaryUnavailableError()
        return res

    @property
    def value(self):
        with self._ensure_exception():
            return self._engine._core.api.exchange.get_internal_variable_value(
                self._engine._core.state,
                variable_handle=self._core_handle
            )


class OutputMeter(
    BaseVariable,
    CoreExceptionableMixin,
    _base_.Component,
):
    @_dataclasses_.dataclass(frozen=True)
    class Ref(BaseVariable.Ref):
        type: str

        def __build__(self):
            return OutputMeter(self)
        
    ref: Ref

    @property
    def _core_handle(self):
        res = self._engine._core.api.exchange.get_meter_handle(
            self._engine._core.state,
            meter_name=self.ref.type,
        )
        if res == -1:
            raise _exceptions_.TemporaryUnavailableError()
        return res

    @property
    def value(self):
        with self._ensure_exception():
            return self._engine._core.api.exchange.get_meter_value(
                self._engine._core.state,
                meter_handle=self._core_handle,
            )


class OutputVariable(
    BaseVariable,
    CoreExceptionableMixin,
    _base_.Component,
):
    @_dataclasses_.dataclass(frozen=True)
    class Ref(BaseVariable.Ref):
        type: str
        key: str

        def __build__(self):
            return OutputVariable(ref=self)

    ref: Ref

    def __attach__(self, engine):
        super().__attach__(engine=engine)
        self._engine._workflows.on(
            'run:pre', 
            lambda _: self._engine._core.api.exchange.request_variable(
                self._engine._core.state,
                variable_name=self.ref.type,
                variable_key=self.ref.key,
            )
        )
        return self

    @property
    def _core_handle(self):
        res = self._engine._core.api.exchange.get_variable_handle(
            self._engine._core.state,
            variable_name=self.ref.type,
            variable_key=self.ref.key,
        )
        if res == -1:
            raise _exceptions_.TemporaryUnavailableError()
        return res

    @property
    def value(self):
        with self._ensure_exception():
            return self._engine._core.api.exchange.get_variable_value(
                self._engine._core.state,
                variable_handle=self._core_handle,
            )


class VariableManager(
    BaseVariableManager, 
    _base_.Component[_worlds_.Engine],
):
    @_functools_.cached_property
    def _instances(self):
        return dict[str | BaseVariable.Ref, BaseVariable]()

    def on(self, ref):
        if ref in self._instances:
            return self
        
        def build(ref: str | BaseVariable.Ref):
            symbols: dict[str, _typing_.Callable[[], BaseVariable]] = {
                'wallclock': lambda: WallClock(WallClock.Ref()),
                'wallclock:calendar': lambda: WallClock(WallClock.Ref(calendar=True)),
            }
            if ref in symbols:
                return symbols[ref]()

            constructors: dict[BaseVariable.Ref, BaseVariable] = {
                WallClock.Ref: WallClock,
                Actuator.Ref: Actuator,
                InternalVariable.Ref: InternalVariable,
                OutputMeter.Ref: OutputMeter,
                OutputVariable.Ref: OutputVariable,
            }
            for ref_cls, constructor in constructors.items():
                if isinstance(ref, ref_cls):
                    return constructor(ref=ref)
                
            raise TypeError(f'Unknown symbol or reference: {ref}.')

        # TODO attach self????
        self._instances[ref] = build(ref).__attach__(self._engine)
        return self

        # TODO depr __build__??? !!!!!!!!!!!
        self._instances[ref] = (
            ref.__build__()
                .__attach__(self._engine)
        )
        return self
    
    def off(self, ref):
        # TODO 
        raise NotImplementedError

    def __contains__(self, ref):
        return self._instances.__contains__(ref)

    def __getitem__(self, ref):
        if not self.__contains__(ref):
            raise _exceptions_.TemporaryUnavailableError(
                f'Reference not available or not turned on: {ref}.'
            )
        return self._instances.__getitem__(ref)
    
    def get(self, ref):
        return self.on(ref=ref)[ref]

    # TODO deprecate
    def getdefault(self, ref):
        return self.on(ref=ref)[ref]
    
    class KeysView(_utils_.mappings.GroupableIterator):
        pass
    
    def keys(self, all: bool = True) -> KeysView:
        # TODO ??
        return self.KeysView(
            iterable=_itertools_.chain(
                (WallClock.Ref(), ),
                (
                    {
                        'Actuator': lambda: Actuator.Ref(
                            type=datapoint.name,
                            key=datapoint.key,
                            control_type=datapoint.type,
                        ),
                        'InternalVariable': lambda: InternalVariable.Ref(
                            type=datapoint.name,
                            key=datapoint.key,
                        ),
                        'OutputMeter': lambda: OutputMeter.Ref(
                            type=datapoint.name,
                        ),
                        'OutputVariable': lambda: OutputVariable.Ref(
                            type=datapoint.name,
                            key=datapoint.key,
                        ),
                        # TODO
                        # 'PluginGlobalVariable', 'PluginTrendVariable'
                    }.get(datapoint.what, lambda: ...)()
                    for datapoint in (
                        self._engine._core.api.exchange
                        .get_api_data(self._engine._core.state)
                    )
                )
            ),
        ) if all else self.KeysView(self._instances.keys())
    
    def __getstate__(self) -> object:
        return super().__getstate__()
    
    def __setstate__(self, state: object):
        return super().__setstate__(state)
        

__all__ = [
    'BaseVariable',
    'BaseVariableManager',
    'WallClock',
    'Actuator',
    'InternalVariable',
    'OutputMeter',
    'OutputVariable',
    'VariableManager',
]

