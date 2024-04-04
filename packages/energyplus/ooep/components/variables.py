import abc as _abc_
import typing as _typing_
import functools as _functools_
import dataclasses as _dataclasses_
import itertools as _itertools_

from . import base as _base_

from .. import (
    exceptions as _exceptions_,
    utils as _utils_,
)


class BaseVariable(_base_.Component, _abc_.ABC):
    class Ref(_abc_.ABC):
        # TODO NOTE this constructs an object according to the reference `Ref`
        @_abc_.abstractmethod
        def __build__(self) -> 'BaseVariable':
            raise NotImplementedError

    def __init__(self, ref: Ref):
        super().__init__()
        self._ref = ref

    @property
    def ref(self):
        return self._ref

    @property
    @_abc_.abstractmethod
    def value(self):
        raise NotImplementedError

class BaseControlVariable(BaseVariable, _abc_.ABC):
    @BaseVariable.value.setter
    @_abc_.abstractmethod
    def value(self, o: _typing_.Any):
        raise NotImplementedError

# TODO 
class BaseVariableManager(_base_.Component, _abc_.ABC):
    @_abc_.abstractmethod
    def on(self, ref: BaseVariable.Ref) -> _typing_.Self:
        raise NotImplementedError

    @_abc_.abstractmethod
    def __getitem__(self, ref: BaseVariable.Ref) -> BaseVariable:
        raise NotImplementedError


class Actuator(
    BaseControlVariable,
    _base_.Component,
):
    @_dataclasses_.dataclass(frozen=True)
    class Ref(BaseControlVariable.Ref):
        type: str
        control_type: str
        key: str

        def __build__(self): 
            return Actuator(ref=self)

    ref: Ref

    @property
    def _core_handle(self):
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
        return self._engine._core.api.exchange.get_actuator_value(
            self._engine._core.state,
            actuator_handle=self._core_handle,
        )

    @value.setter
    def value(self, n: float):
        self._engine._core.api.exchange.set_actuator_value(
            self._engine._core.state,
            actuator_handle=self._core_handle,
            actuator_value=float(n),
        )

    def reset(self):
        self._engine._core.api.exchange.reset_actuator(
            self._engine._core.state,
            actuator_handle=self._core_handle,
        )


class InternalVariable(
    BaseVariable,
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
        return self._engine._core.api.exchange.get_internal_variable_value(
            self._engine._core.state,
            variable_handle=self._core_handle
        )


class OutputMeter(
    BaseVariable,
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
        return self._engine._core.api.exchange.get_meter_value(
            self._engine._core.state,
            meter_handle=self._core_handle,
        )


class OutputVariable(
    BaseVariable,
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
        # TODO energyplus error flag!!!!!!!!!!!!!!!!!!!!!!
        return self._engine._core.api.exchange.get_variable_value(
            self._engine._core.state,
            variable_handle=self._core_handle,
        )




import datetime as _datetime_

class WallClock(
    BaseVariable,
    _base_.Component,
):
    @_dataclasses_.dataclass(frozen=True)
    class Ref(BaseVariable.Ref):
        def __build__(self):
            return WallClock(ref=self)

    ref: Ref

    @property
    def value(self):
        api = self._engine._core.api.exchange
        state = self._engine._core.state
        # TODO err flag temp unavailable!!!!!!!!!!!
        return _datetime_.datetime(
            # NOTE see https://github.com/NREL/EnergyPlus/issues/10210
            # TODO .calendar_year v .year
            year=api.calendar_year(state),
            month=api.month(state),
            day=api.day_of_month(state),
            hour=api.hour(state),
            # TODO NOTE energyplus api returns 0?-60: datetime requires range(60)
            minute=api.minutes(state) % _datetime_.datetime.max.minute,
        )


class VariableManager(BaseVariableManager, _base_.Component):
    @_functools_.cached_property
    def _variable_data(self) -> _typing_.Mapping[
        BaseVariable.Ref, 
        BaseVariable,
    ]:
        return dict()

    def on(self, ref):
        if ref in self._variable_data:
            return self
        self._variable_data[ref] = (
            ref.__build__()
                .__attach__(self._engine)
        )
        return self
    
    # TODO 
    def off(self, ref):
        raise NotImplementedError

    def __contains__(self, ref):
        return self._variable_data.__contains__(ref)

    def __getitem__(self, ref):
        if not self.__contains__(ref):
            raise _exceptions_.TemporaryUnavailableError()
        return self._variable_data.__getitem__(ref)
    
    def ondefault(self, ref):
        return self.on(ref=ref)[ref]
    
    # TODO
    # TODO additional features: ipytree, dataframe view??? thru plugin system
    class KeysView(_utils_.mappings.GroupableIterator):
        pass
    
    def keys(self) -> KeysView:
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
        )
        

__all__ = [
    BaseVariable,
    BaseVariableManager,
    Actuator,
    InternalVariable,
    OutputMeter,
    OutputVariable,
    WallClock,
    VariableManager,
]

