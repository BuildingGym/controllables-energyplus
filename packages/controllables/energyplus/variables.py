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
import warnings as _warnings_
from typing import Callable, Generic, TypeVar

from . import (
    world as _world_,
)

from controllables.core import (
    # TODO rm dep
    utils as _utils_,
)
from controllables.core.errors import (
    TemporaryUnavailableError,
)
from controllables.core.components import (
    BaseComponent,
)
from controllables.core.variables import (
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
                    f'Core API data exchange error: {self}'
                )


_ValT = TypeVar('_ValT')


class Variable(
    Generic[_ValT],
    VariableNumOpsMixin,
    BaseVariable[_ValT], 
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
    Generic[_ValT],
    Variable[_ValT],
    BaseMutableVariable, 
    BaseComponent['VariableManager'],
):
    r"""
    Base mutable variable for all mutable variables in this module.
    """
    
    pass


import datetime as _datetime_

class WallClock(Variable[_datetime_.datetime], CoreExceptionableMixin):
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

        #with self._ensure_exception():
        try: 
            return _datetime_.datetime.min.replace(
                year=(
                    exchange.calendar_year(state) 
                    if self.ref.calendar else 
                    exchange.year(state)
                ),
            ) + _datetime_.timedelta(
                days=exchange.day_of_year(state) - 1,
                hours=exchange.current_time(state),
            )
        except ValueError:
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

        core = self._manager._core

        @core.hooks['run:pre'].on
        def request(*args, **kwargs):
            core.api.exchange \
                .request_variable(
                    core.state,
                    variable_name=self.ref.type,
                    variable_key=self.ref.key,
                )
            
        request()
        if core.running:
            _warnings_.warn(
                f'{self} requested while {core} is running; '
                f'It may not be available until the next run',
                RuntimeWarning,
            )
            
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
    
    _symbols: dict[str, Callable[[], Variable]] = {
        # std
        'time': lambda: WallClock(WallClock.Ref(calendar=True)),
        # ...
        'wallclock': lambda: WallClock(WallClock.Ref()),
        'wallclock:calendar': lambda: WallClock(WallClock.Ref(calendar=True)),
    }

    _constructors: dict[Variable.Ref, Variable] = {
        WallClock.Ref: WallClock,
        Actuator.Ref: Actuator,
        InternalVariable.Ref: InternalVariable,
        OutputMeter.Ref: OutputMeter,
        OutputVariable.Ref: OutputVariable,
    }
                
    # TODO
    def __missing__(self, ref):
        def build(ref: str | Variable.Ref) -> Variable:
            if ref in self._symbols:
                return self._symbols[ref]()            
            
            for ref_cls, constructor in self._constructors.items():
                if isinstance(ref, ref_cls):
                    return constructor(ref=ref)
                
            raise TypeError(f'Unknown symbol or reference: {ref}')
        
            # TODO attach here
            # ...

        self[ref] = build(ref).__attach__(self)

        return self[ref]
    
    def __contains__(self, ref):
        return any((
            ref in self._symbols, 
            isinstance(ref, tuple(self._constructors.keys())),
        ))

    def __delitem__(self, ref):
        return super(dict).__delitem__(ref)
    
    def __repr__(self):
        return object.__repr__(self)

    class KeysView(_utils_.mappings.GroupableIterator):
        r"""TODO"""

        def dataframes(self, **pandas_kwds):
            # TODO
            from controllables.core.errors import (
                OptionalModuleNotFoundError,
            )
                        
            try: import pandas as _pandas_
            except ModuleNotFoundError as e:
                raise OptionalModuleNotFoundError.suggest(['pandas']) from e
            
            return {
                ref_type: _pandas_.DataFrame(refs, **pandas_kwds)
                for ref_type, refs in self.group(type).items()
            }

        def _repr_html_(self):
            import warnings as _warnings_

            from controllables.core.errors import (
                OptionalModuleNotFoundError,
                OptionalModuleNotFoundWarning,
            )
            from controllables.core.utils.ipy import repr_html

            try: import pandas as _pandas_
            except ModuleNotFoundError as e:
                raise OptionalModuleNotFoundError.suggest(['pandas']) from e

            def repr_htmltable(df: _pandas_.DataFrame):                
                try: import itables as _itables_
                except ModuleNotFoundError:
                    _warnings_.warn(
                        OptionalModuleNotFoundWarning.suggest(['itables'])
                    )
                    return df.to_html()

                return _itables_.to_html_datatable(
                    df, 
                    classes='display',
                    layout={'bottom': 'searchPanes'},
                    searchPanes={'initCollapsed': True},
                    maxBytes=0,
                )

            return (
                # TODO BUG itables wont render if first hidden?
                ''.join(
                    rf'''
                    <details open>
                        <summary>{repr_html(ref_type)}</summary>
                        <figure>{repr_htmltable(refs_df)}</figure>
                    </details>
                    '''
                    for ref_type, refs_df in self.dataframes().items()
                )
            )
    
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
