import typing as _typing_

from .. import base as _base_
from ... import exceptions as _exceptions_
from ...components.events import (
    Event
)
from ...components.variables import (
    BaseVariable
)

# TODO
try: 
    import plotly as _plotly_
    import plotly.basedatatypes as _plotly_types_
except ImportError as e:
    raise _base_.OptionalImportError(['plotly']) from e


class TraceAdapter(_base_.Addon):
    def __init__(
        self, 
        target: _plotly_types_.BaseTraceType, 
        prop_bindings: dict[
            str, 
            str | BaseVariable.Ref | BaseVariable
            | _typing_.Iterator | _typing_.Sequence,
        ],
    ):
        if not isinstance(target, _plotly_types_.BaseTraceType):
            raise TypeError(f'Unsupported target: {target}.')
        self._target = target
        self._prop_bindings = prop_bindings

    def update(self):
        def assign(value):
            self._target[prop] = tuple(value)
        
        def extend(value):                
            self._target[prop] = (
                (self._target[prop] 
                 if self._target[prop] is not None else 
                 tuple()) + tuple(value)
            )

        for prop, binding in self._prop_bindings.items():
            if isinstance(binding, (str, BaseVariable.Ref)):
                binding = self._engine.variables.get(binding)
            if isinstance(binding, BaseVariable):
                try: extend((binding.value,))
                except _exceptions_.TemporaryUnavailableError:
                    extend((None,))
                continue
            if isinstance(binding, _typing_.Iterator):
                try: extend(next(binding),)
                except StopIteration:
                    extend((None,))
                continue
            if isinstance(binding, _typing_.Sequence):
                assign(binding)
                continue
            raise TypeError(f'Unsupported binding: {binding}.')
        
    def select(self, s: slice | int):
        for prop, _ in self._prop_bindings.items():
            if self._target[prop] is None:
                continue
            self._target[prop] = self._target[prop][s]
        

import functools as _functools_


class FigureProvider(_base_.Addon):
    r"""
    TODO

    Example usage:

    .. code-block:: python
        #FigureProvider().add('scatter', {'x': ..., 'y': ...}).update('new_enviornment')
        #FigureProvider().add({'type': 'scatter', 'name': 'myfavoritescatter'}, {'x': ..., 'y': ...}).update('new_enviornment')

    """

    def __init__(
        self, 
        size: int | None = None,
        event_ref: Event.Ref | None = None,
        figure_ref: _plotly_types_.BaseFigure | None = None,
    ):
        r"""
        Initialize the `FigureProvider` with an optional size, event reference, and figure reference.

        :param size: 
            The maximum number of the datapoints to display (and keep). 
            If not provided, all data is displayed.
        :param event_ref:
            The event reference to trigger the update.
        :param figure_ref:
            The reference to the Plotly figure to use. 
            If not provided, a new figure is created.
        """

        super().__init__()
        self._size = size
        self._event_ref = event_ref
        self._figure_ref = figure_ref
        self._trace_adapters: list[TraceAdapter] = []

    def __attach__(self, engine):
        super().__attach__(engine)

        for t in self._trace_adapters:
            t.__attach__(self._engine)
        
        if self._event_ref is not None:
            self._engine.events.on(
                self._event_ref, 
                lambda _, self=self: self.update(),
            )

        return self

    @_functools_.cached_property
    def figure(self):
        return (
            _plotly_.graph_objs.FigureWidget() 
            if self._figure_ref is None else 
            self._figure_ref
        )

    def add(
        self, 
        trace: _plotly_types_.BaseTraceType, 
        prop_bindings: dict, 
        **plotly_kwds,
    ):
        # TODO rm
        #if isinstance(trace, str):
        #    trace = {'type': trace}
        self.figure.add_trace(trace, **plotly_kwds)
        self._trace_adapters.append(
            # TODO NOTE doc
            TraceAdapter(self.figure.data[-1], prop_bindings=prop_bindings)
        )
        return self
    
    def update(self):
        with self.figure.batch_update():
            for t in self._trace_adapters:
                t.update()
                if self._size is not None:
                    t.select(slice(-self._size, None))                
        return self


__all__ = [
    'FigureProvider',
]