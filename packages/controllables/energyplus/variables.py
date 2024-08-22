r"""
Variables.

Scope: Variable management.

.. note:: 
    :class:`Variable`-s within this module
    are not meant to be instantiated directly by users. 
    Access instances of those classes via :class:`VariableManager`.
"""


import abc as _abc_
import dataclasses as _dataclasses_
import itertools as _itertools_
import contextlib as _contextlib_
from typing import Callable

from . import (
    world as _world_,
)

# TODO rm dep
from controllables.core import (
    utils as _utils_,
    BaseComponent,
    TemporaryUnavailableError,
)

from controllables.core.specs.variables import (
    BaseVariable,
    BaseMutableVariable,
    BaseVariableManager,
    VariableNumOpsMixin,
)


class CoreExceptionableMixin(
    BaseComponent['VariableManager'],
):
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
            api = self._manager._core.api
            state = self._manager._core.state
            if api.exchange.api_error_flag(state):
                api.exchange.reset_api_error_flag(state)
                raise TemporaryUnavailableError(
                    'Core API data exchange error'
                )


class Variable(
    VariableNumOpsMixin,
    BaseVariable, 
    BaseComponent['VariableManager'],
):
    r"""
    Base variable for all variables in this module.
    Managed by :class:`VariableManager`.
    """

    class Ref(_abc_.ABC):
        r"""Variable reference."""
        ...

    def __init__(self, ref: Ref):
        r"""
        Initialize the variable.

        :param ref: The reference to the variable.
        """

        super().__init__()
        self._ref = ref

    @property
    def ref(self) -> Ref:
        r"""Get the reference to this variable."""

        return self._ref
    
class MutableVariable(
    Variable,
    BaseMutableVariable, 
    BaseComponent['VariableManager'],
):
    r"""
    Base mutable variable for all mutable variables in this module.
    """
    
    pass


import datetime as _datetime_

class WallClock(Variable, CoreExceptionableMixin):
    r"""Wall clock variable class."""

    @_dataclasses_.dataclass(frozen=True)
    class Ref(Variable.Ref):
        r"""
        Reference to a wall clock.
        
        :param calendar: 
            Whether to use the calendar year or the simulation year.
            If `True`, this reference refers to a calendar wall clock.

        .. seealso::
            * https://github.com/NREL/EnergyPlus/issues/10210
        """

        calendar: bool = False

    ref: Ref

    # TODO FIXME .minute
    @property
    def value(self):
        exchange = self._manager._core.api.exchange
        state = self._manager._core.state
        try:
            return _datetime_.datetime(
                year=(
                    exchange.calendar_year(state) 
                    if self.ref.calendar else 
                    exchange.year(state)
                ),
                month=exchange.month(state),
                day=exchange.day_of_month(state),
                # TODO
                hour=exchange.hour(state),
                # NOTE core api returns 1-60: datetime requires range(60)
                minute=exchange.minutes(state) - 1,
                # TODO
                tzinfo=_datetime_.timezone(offset=_datetime_.timedelta(0)),
            )
        except ValueError as e:
            # 
            # TODO better handling!!!!!!!!!!!!!
            # TODO err flag temp unavailable!!!!!!!!!!!
            raise TemporaryUnavailableError()



class Actuator(
    MutableVariable,
    CoreExceptionableMixin,
):
    r"""
    Actuator variable class.
    """

    @_dataclasses_.dataclass(frozen=True)
    class Ref(MutableVariable.Ref):
        r"""
        Reference to an actuator.

        :param type: The type of the actuator.
        :param control_type: The control type of the actuator.
        :param key: The key of the actuator.

        Examples:
        
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

    ref: Ref

    @property
    def _core_handle(self):
        r"""
        Get the internal handle of the actuator.

        :raises: :class:`TemporaryUnavailableError` if the handle is not available.

        ...seealso:: 
            * https://energyplus.readthedocs.io/en/latest/datatransfer.html#datatransfer.DataExchange.get_actuator_handle
        """
        res = self._manager._core.api.exchange \
            .get_actuator_handle(
                self._manager._core.state,
                component_type=self.ref.type,
                control_type=self.ref.control_type,
                actuator_key=self.ref.key,
            )
        if res == -1:
            raise TemporaryUnavailableError() 
        return res

    @property
    def value(self):
        r"""
        Get the value of the actuator.

        :raises: :class:`TemporaryUnavailableError` if the value is not available.
        """
        with self._ensure_exception():
            return self._manager._core.api.exchange \
                .get_actuator_value(
                    self._manager._core.state,
                    actuator_handle=self._core_handle,
                )

    @value.setter
    def value(self, n: float):
        r"""
        Set the value of the actuator.

        :param n: The value to set the actuator to.
        """
        self._manager._core.api.exchange \
            .set_actuator_value(
                self._manager._core.state,
                actuator_handle=self._core_handle,
                actuator_value=float(n),
            )

    def reset(self):
        r"""
        Reset the actuator.
        This transfers the control of the actuator back to attached engine.

        ...seealso:: https://energyplus.readthedocs.io/en/latest/datatransfer.html#datatransfer.DataExchange.reset_actuator
        """
        self._manager._core.api.exchange \
            .reset_actuator(
                self._manager._core.state,
                actuator_handle=self._core_handle,
            )


class InternalVariable(
    Variable,
    CoreExceptionableMixin,
):
    r"""
    Internal variable class.
    """

    @_dataclasses_.dataclass(frozen=True)
    class Ref(Variable.Ref):
        type: str
        key: str

    ref: Ref

    @property
    def _core_handle(self):
        res = self._manager._core.api.exchange \
            .get_internal_variable_handle(
                self._manager._core.state,
                variable_name=self.ref.type,
                variable_key=self.ref.key
            )
        if res == -1:
            raise TemporaryUnavailableError()
        return res

    @property
    def value(self):
        with self._ensure_exception():
            return self._manager._core.api.exchange \
                .get_internal_variable_value(
                    self._manager._core.state,
                    variable_handle=self._core_handle
                )


class OutputMeter(
    Variable,
    CoreExceptionableMixin,
):
    r"""
    Output meter class.

    """

    @_dataclasses_.dataclass(frozen=True)
    class Ref(Variable.Ref):
        type: str
        
    ref: Ref

    @property
    def _core_handle(self):
        res = self._manager._core.api.exchange \
            .get_meter_handle(
                self._manager._core.state,
                meter_name=self.ref.type,
            )
        if res == -1:
            raise TemporaryUnavailableError()
        return res

    @property
    def value(self):
        with self._ensure_exception():
            return self._manager._core.api.exchange \
                .get_meter_value(
                    self._manager._core.state,
                    meter_handle=self._core_handle,
                )


class OutputVariable(
    Variable,
    CoreExceptionableMixin,
):
    r"""
    Output variable class.
    """

    @_dataclasses_.dataclass(frozen=True)
    class Ref(Variable.Ref):
        type: str
        key: str

    ref: Ref

    def __attach__(self, engine):
        super().__attach__(manager=engine)

        world = self._manager._manager

        @world.workflows['run:pre'].use
        def request_var(_=None):
            world._core.api.exchange \
                .request_variable(
                    world._core.state,
                    variable_name=self.ref.type,
                    variable_key=self.ref.key,
                )
            
        # TODO
        request_var()

        match world._state:
            case world.State.IDLE:
                #request_var()
                pass
            case _:
                pass
            
        return self

    @property
    def _core_handle(self):
        res = self._manager._core.api.exchange \
            .get_variable_handle(
                self._manager._core.state,
                variable_name=self.ref.type,
                variable_key=self.ref.key,
            )
        if res == -1:
            raise TemporaryUnavailableError()
        return res

    @property
    def value(self):
        with self._ensure_exception():
            return self._manager._core.api.exchange \
                .get_variable_value(
                    self._manager._core.state,
                    variable_handle=self._core_handle,
                )


class VariableManager(
    dict[str | Variable.Ref, Variable],
    BaseVariableManager, 
    BaseComponent[_world_.World],
):
    r"""
    Variable manager.

    TODO
    """

    @property
    def _core(self):
        return self._manager._core
        
    # TODO
    def __missing__(self, ref):
        def build(ref: str | Variable.Ref) -> Variable:
            symbols: dict[str, Callable[[], Variable]] = {
                'wallclock': lambda: WallClock(WallClock.Ref()),
                'wallclock:calendar': lambda: WallClock(WallClock.Ref(calendar=True)),
            }

            constructors: dict[Variable.Ref, Variable] = {
                WallClock.Ref: WallClock,
                Actuator.Ref: Actuator,
                InternalVariable.Ref: InternalVariable,
                OutputMeter.Ref: OutputMeter,
                OutputVariable.Ref: OutputVariable,
            }

            if ref in symbols:
                return symbols[ref]()            
            
            for ref_cls, constructor in constructors.items():
                if isinstance(ref, ref_cls):
                    return constructor(ref=ref)
                
            raise TypeError(f'Unknown symbol or reference: {ref}')

        self[ref] = build(ref).__attach__(self)

        return self[ref]

    def __delitem__(self, ref):
        return super(dict).__delitem__(ref)
    
    def __repr__(self):
        return object.__repr__(self)

    # TODO
    class KeysView(_utils_.mappings.GroupableIterator):
        pass
    
    def available_keys(self) -> KeysView:
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
                            # TODO https://energyplus.readthedocs.io/en/latest/datatransfer.html#datatransfer.DataExchange.APIDataExchangePoint.key
                            type=datapoint.key, # .name
                        ),
                        'OutputVariable': lambda: OutputVariable.Ref(
                            type=datapoint.name,
                            key=datapoint.key,
                        ),
                        # TODO
                        # 'PluginGlobalVariable', 'PluginTrendVariable'
                    }
                    .get(datapoint.what, lambda: None)()
                    for datapoint in (
                        self._core.api.exchange
                        .get_api_data(self._core.state)
                    )
                )
            ),
        )
    
    def __getstate__(self) -> object:
        return super().__getstate__()
    
    def __setstate__(self, state: object):
        return super().__setstate__(state)


__all__ = [
    'WallClock',
    'Actuator',
    'InternalVariable',
    'OutputMeter',
    'OutputVariable',
    'VariableManager',
]
