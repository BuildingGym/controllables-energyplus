r"""
Variables.

.. note:: 
    :class:`Variable`-s within this module
    are not meant to be instantiated directly by users. 
    Access instances of those classes via :class:`VariableManager`.
"""


import abc as _abc_
import dataclasses as _dataclasses_
import itertools as _itertools_
import contextlib as _contextlib_
import functools as _functools_
import warnings as _warnings_
from typing import Callable, Generic, TypeVar

# TODO rm dep
from controllables.core.utils.mappings import GroupableIterator
from controllables.core.errors import (
    TemporaryUnavailableError,
)
from controllables.core.components import (
    Component,
)
from controllables.core.variables import (
    BaseVariable,
    BaseMutableVariable,
    BaseVariableManager,
    MutableVariable,
)

from .systems import System


_ValT = TypeVar('_ValT')


class CommonVariable(
    Generic[_ValT],
    BaseVariable[_ValT], 
    Component['VariableManager'],
):
    r"""
    Common class for all variables in this module.
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

    def __repr__(self):
        return f'{type(self).__name__}({self.ref!r})'

    @property
    def ref(self) -> Ref:
        r"""Get the reference to this variable."""

        return self._ref
    
    @property
    def _kernel(self):
        return self.parent._kernel
    
    @_contextlib_.contextmanager
    def _ensure_exception(self):
        r"""
        Ensure kernel API exceptions caught and relevant errors raised.

        :raises: :class:`TemporaryUnavailableError` if an error has occurred.

        .. seealso:: 
        https://energyplus.readthedocs.io/en/latest/datatransfer.html#datatransfer.DataExchange.api_error_flag
        """
        
        try:
            yield
        finally:
            api = self._kernel.api
            state = self._kernel.state
            if api.exchange.api_error_flag(state):
                api.exchange.reset_api_error_flag(state)
                raise TemporaryUnavailableError(
                    f'Kernel API data exchange error: {self!r}'
                )


class CommonMutableVariable(
    Generic[_ValT],
    CommonVariable[_ValT],
    BaseMutableVariable, 
    Component['VariableManager'],
):
    r"""
    Base mutable variable for all mutable variables in this module.
    """
    
    pass


# TODO make readonly
class RunIndicator(
    CommonVariable[bool],
    MutableVariable[bool], 
    Component['VariableManager'],
):
    r"""
    Run indicator variable class.
    """

    def __init__(self):
        super().__init__(ref=None)

    def __attach__(self, parent):
        super().__attach__(parent)

        self.value = False

        @self._kernel.hooks['run:pre'].on
        def _(*args, **kwargs):
            self.value = True

        @self._kernel.hooks['run:post'].on
        def _(*args, **kwargs):
            self.value = False

        return self


import datetime as _datetime_

class WallClock(CommonVariable[_datetime_.datetime]):
    r"""Wall clock variable class."""

    @_dataclasses_.dataclass(frozen=True)
    class Ref(CommonVariable.Ref):
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

    @property
    def value(self):
        exchange = self._kernel.api.exchange
        state = self._kernel.state

        # TODO
        with self._ensure_exception():
            try: 
                return _datetime_.datetime.min.replace(
                    year=(
                        exchange.calendar_year(state) 
                        if self.ref.calendar else 
                        exchange.year(state)
                    ),
                    tzinfo=_datetime_.timezone(offset=_datetime_.timedelta(0)),
                ) + _datetime_.timedelta(
                    days=exchange.day_of_year(state) - 1,
                    hours=exchange.current_time(state),
                )
            except ValueError as e:
                raise TemporaryUnavailableError(f'{self!r}') from e


class Actuator(CommonMutableVariable):
    r"""
    Actuator variable class.
    """

    @_dataclasses_.dataclass(frozen=True)
    class Ref(CommonMutableVariable.Ref):
        r"""
        Reference to an actuator.

        :param type: The type of the actuator.
        :param control_type: The control type of the actuator.
        :param key: The key of the actuator.
        """

        type: str
        control_type: str
        key: str

    ref: Ref

    @_functools_.cached_property
    def _kernel_handle(self):
        r"""
        Get the internal handle of the actuator.

        :raises: :class:`TemporaryUnavailableError` if the handle is not available.

        .. seealso:: 
        * https://energyplus.readthedocs.io/en/latest/datatransfer.html#datatransfer.DataExchange.get_actuator_handle
        """

        kernel = self._kernel

        res = kernel.api.exchange \
            .get_actuator_handle(
                kernel.state,
                component_type=self.ref.type,
                control_type=self.ref.control_type,
                actuator_key=self.ref.key,
            )
        if res == -1:
            raise TemporaryUnavailableError(f'{self!r}') 
        
        @kernel.hooks['reset:post'].on
        def _cleanup(*args, **kwargs):
            kernel.hooks['reset:post'].off(_cleanup)
            del self._kernel_handle

        return res

    @property
    def value(self):
        r"""
        Get the value of the actuator.

        :raises: :class:`TemporaryUnavailableError` if the value is not available.
        """

        with self._ensure_exception():
            return self._kernel.api.exchange \
                .get_actuator_value(
                    self._kernel.state,
                    actuator_handle=self._kernel_handle,
                )

    @value.setter
    def value(self, n):
        r"""
        Set the value of the actuator.

        :param n: The value to set the actuator to.
        """

        self._kernel.api.exchange \
            .set_actuator_value(
                self._kernel.state,
                actuator_handle=self._kernel_handle,
                actuator_value=float(n),
            )

    def reset(self):
        r"""
        Reset the actuator.
        This transfers the control of the actuator back to attached engine.

        .. seealso:: 
        <https://energyplus.readthedocs.io/en/latest/datatransfer.html#datatransfer.DataExchange.reset_actuator>
        """

        self._kernel.api.exchange \
            .reset_actuator(
                self._kernel.state,
                actuator_handle=self._kernel_handle,
            )


class InternalVariable(CommonVariable):
    r"""
    Internal variable class.
    """

    @_dataclasses_.dataclass(frozen=True)
    class Ref(CommonVariable.Ref):
        type: str
        key: str

    ref: Ref

    @_functools_.cached_property
    def _kernel_handle(self):
        kernel = self._kernel

        res = kernel.api.exchange \
            .get_internal_variable_handle(
                kernel.state,
                variable_type=self.ref.type,
                variable_key=self.ref.key
            )
        if res == -1:
            raise TemporaryUnavailableError(f'{self!r}')

        @kernel.hooks['reset:post'].on
        def _cleanup(*args, **kwargs):
            kernel.hooks['reset:post'].off(_cleanup)
            del self._kernel_handle

        return res

    @property
    def value(self):
        with self._ensure_exception():
            return self._kernel.api.exchange \
                .get_internal_variable_value(
                    self._kernel.state,
                    variable_handle=self._kernel_handle
                )


class OutputMeter(CommonVariable):
    r"""
    Output meter class.

    """

    @_dataclasses_.dataclass(frozen=True)
    class Ref(CommonVariable.Ref):
        type: str
        
    ref: Ref

    @_functools_.cached_property
    def _kernel_handle(self):
        kernel = self._kernel

        res = kernel.api.exchange \
            .get_meter_handle(
                kernel.state,
                meter_name=self.ref.type,
            )
        if res == -1:
            raise TemporaryUnavailableError(f'{self!r}')

        @kernel.hooks['reset:post'].on
        def _cleanup(*args, **kwargs):
            kernel.hooks['reset:post'].off(_cleanup)
            del self._kernel_handle

        return res

    @property
    def value(self):
        with self._ensure_exception():
            return self._kernel.api.exchange \
                .get_meter_value(
                    self._kernel.state,
                    meter_handle=self._kernel_handle,
                )


class OutputVariable(CommonVariable):
    r"""
    Output variable class.
    """

    @_dataclasses_.dataclass(frozen=True)
    class Ref(CommonVariable.Ref):
        type: str
        key: str

    ref: Ref

    def __attach__(self, engine):
        super().__attach__(parent=engine)

        kernel = self._kernel

        @kernel.hooks['run:pre'].on
        def request(*args, **kwargs):
            kernel.api.exchange \
                .request_variable(
                    kernel.state,
                    variable_name=self.ref.type,
                    variable_key=self.ref.key,
                )
            
        request()
        if kernel.running:
            _warnings_.warn(
                f'{self!r} requested while {kernel!r} is running; '
                f'It may not be available until the next run. '
                f'More info: https://energyplus.readthedocs.io'
                f'/en/latest/datatransfer.html'
                f'#datatransfer.DataExchange.request_variable',
                RuntimeWarning,
            )
            
        return self
    
    @_functools_.cached_property
    def _kernel_handle(self):
        kernel = self._kernel

        res = kernel.api.exchange \
            .get_variable_handle(
                kernel.state,
                variable_name=self.ref.type,
                variable_key=self.ref.key,
            )
        if res == -1:
            raise TemporaryUnavailableError(f'{self!r}')
        
        @kernel.hooks['reset:post'].on
        def _cleanup(*args, **kwargs):
            kernel.hooks['reset:post'].off(_cleanup)
            del self._kernel_handle

        return res

    @property
    def value(self):
        with self._ensure_exception():
            return self._kernel.api.exchange \
                .get_variable_value(
                    self._kernel.state,
                    variable_handle=self._kernel_handle,
                )


# TODO
import functools as _functools_


class VariableManager(
    #dict[str | Variable.Ref, Variable],
    BaseVariableManager[str | CommonVariable.Ref, CommonVariable], 
    Component[System],
):
    r"""
    Variable manager class.

    TODO
    """

    # TODO mv VariableManager to core
    @_functools_.cached_property
    def _variables(self):
        return dict()

    @property
    def _kernel(self):
        return self.parent._kernel
    
    _symbols: dict[str, Callable[[], CommonVariable]] = {
        # std
        'running': lambda: RunIndicator(),
        'time': lambda: WallClock(WallClock.Ref(calendar=True)),
        # ...
        'wallclock': lambda: WallClock(WallClock.Ref()),
        'wallclock:calendar': lambda: WallClock(WallClock.Ref(calendar=True)),
    }

    _constructors: dict[CommonVariable.Ref, CommonVariable] = {
        WallClock.Ref: WallClock,
        Actuator.Ref: Actuator,
        InternalVariable.Ref: InternalVariable,
        OutputMeter.Ref: OutputMeter,
        OutputVariable.Ref: OutputVariable,
    }
                
    # TODO
    def __getitem__(self, ref) -> CommonVariable:
        def build(ref: str | CommonVariable.Ref) -> CommonVariable:
            if ref in self._symbols:
                return self._symbols[ref]()            
            
            for ref_cls, constructor in self._constructors.items():
                if isinstance(ref, ref_cls):
                    return constructor(ref=ref)
                
            raise TypeError(f'Unknown symbol or reference: {ref}')
        
            # TODO attach here
            # ...

        if ref in self._variables:
            return self._variables[ref]

        self._variables[ref] = build(ref).attach(self)
        return self._variables[ref]
    
    def __contains__(self, ref):
        return any((
            ref in self._symbols, 
            isinstance(ref, tuple(self._constructors.keys())),
        ))

    def __delitem__(self, ref):
        # TODO detach
        return super(dict).__delitem__(ref)
    
    def __repr__(self):
        return object.__repr__(self)

    class KeysView(GroupableIterator):
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
                        self._kernel.api.exchange
                        .get_api_data(self._kernel.state)
                    )
                )
            ),
        )
    
    # TODO
    # def __getstate__(self) -> object:
    #     return super().__getstate__()
    
    # def __setstate__(self, state: object):
    #     return super().__setstate__(state)


__all__ = [
    'WallClock',
    'Actuator',
    'InternalVariable',
    'OutputMeter',
    'OutputVariable',
    'VariableManager',
]
