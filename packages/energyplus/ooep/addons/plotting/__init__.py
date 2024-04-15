from __future__ import annotations

# TODO variable viz
# TODO mpl svg animations https://github.com/matplotlib/matplotlib/issues/19694
import typing as _typing_

from ... import (
    components as _components_,
    exceptions as _exceptions_,
)
from .. import base as _base_
# TODO
#from . import utils as _utils_
from .utils import (
    CoordinateView,
    Line2DProvider,
    LineChart2DProvider,
)


class VariableLine2DProvider(Line2DProvider, _base_.Addon):
    def __init__(
        self, 
        # TODO typing!!!!!!
        data_ref: _typing_.Callable[[], _typing_.Any], #| _components_.variables.BaseVariable.Ref,
        event_ref: _components_.events.Event.Ref = None,
        **kwargs,
    ):
        self.var_refs = []
        self.event_ref = event_ref
        if isinstance(data_ref, _typing_.Callable):
            pass
        else:
            def transform(func_or_var):
                nonlocal self
                if isinstance(func_or_var, _components_.variables.BaseVariable.Ref):
                    # TODO
                    self.var_refs.append(func_or_var)
                    return lambda v=func_or_var: self._engine.variables[v].value
                return func_or_var
            data_ref = (
                CoordinateView(ndim=2)
                .map(
                    data_ref, transform, 
                    base_dtype=object,
                )
            )
        super().__init__(data_ref, **kwargs)

    # TODO performance, async update
    def update(self):
        try: super().update()
        except _exceptions_.TemporaryUnavailableError:
            pass

    def __attach__(self, engine):
        super().__attach__(engine=engine)

        for var_ref in self.var_refs:
            self._engine.variables.on(var_ref)

        if self.event_ref is not None:
            self._engine.events.on(
                self.event_ref, 
                lambda _, self=self: self.update(),
            )

        return self

class VariableLineChart2DProvider(LineChart2DProvider, _base_.Addon):
    lines: list[VariableLine2DProvider]

    def __init__(self, event_ref: _components_.events.Event.Ref = None):
        super().__init__(line_factory=VariableLine2DProvider)
        self.event_ref = event_ref

    def __attach__(self, engine):
        super().__attach__(engine=engine)
        
        for line in self.lines:
            line.__attach__(self._engine)

        # TODO !!!!!!!
        if self.event_ref is not None:
            self._engine.events.on(
                self.event_ref, 
                lambda _, self=self: self.update(),
            )

        return self


import matplotlib as _matplotlib_
import matplotlib.dates

class VariableTrendChart2DProvider(VariableLineChart2DProvider, _base_.Addon):
    def __init__(self, event_ref: _typing_.Hashable = None):
        super().__init__(event_ref)
        self.ax.xaxis.set_major_locator(
            _matplotlib_.dates.AutoDateLocator()
        )
        self.ax.xaxis.set_major_formatter(
            _matplotlib_.dates.ConciseDateFormatter(
                self.ax.xaxis.get_major_locator()
            )
        )

    # TODO type hints
    def add(self, var_ref: ..., *args, **kwargs):
        super().add(
            (_components_.variables.WallClock.Ref(), var_ref),
            update_method='extend',
            label=repr(var_ref),
            *args, **kwargs,
        )
        return self


__all__ = [
    'VariableLine2DProvider',
    'VariableLineChart2DProvider',
    'VariableTrendChart2DProvider'
]