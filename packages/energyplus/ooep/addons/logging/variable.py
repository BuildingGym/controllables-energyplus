r"""
Variable Logging.

Scope: Logging and presenting variable values.
"""

import typing as _typing_
import collections as _collections_


from .. import base as _base_
from ... import (
    exceptions as _exceptions_,
)
from ...components.variables import (
    BaseVariable
)
from ...components.events import (
    Event
)


try: 
    import plotly as _plotly_
    import plotly.basedatatypes as _plotly_types_
except ImportError as e:
    raise _base_.OptionalImportError(['plotly']) from e

class TraceSpec(_typing_.TypedDict):
    bindings: dict[
        str, 
        str | BaseVariable.Ref
        | _typing_.Iterator,
    ]

class FigureWidget(_plotly_.graph_objs.FigureWidget):
    def __init__(
        self, 
        logger: 'VariableLogger',
        trace_specs: list[TraceSpec], 
        **plotly_kwds,
    ):
        super().__init__(
            data=[
                {k: v for k, v in trace_spec.items() if k != 'bindings'}
                for trace_spec in trace_specs
            ], 
            **plotly_kwds,
        )
        self._bindings: list[dict] = [
            s.get('bindings', dict()) for s in trace_specs
        ]
        self._logger = logger

    def update(self):
        with self.batch_update():
            for i, trace in enumerate(self.data):
                for prop, ref in self._bindings[i].items():
                    trace[prop] = list(self._logger[ref])
        
        return self


class VariableLogger(_base_.Addon):
    r"""
    A logger that logs variable values over time.

    Example usage:

    .. code-block:: python
        VariableLogger().add('wallclock').add(iter(range(10)))
        
        VariableLogger(maxlen=100).plot([
            dict(
                type='scattergl',
                bindings=dict(
                    x='wallclock:calendar', 
                    y=_ooep_.OutputVariable.Ref(
                        type='People Air Temperature',
                        key='CORE_MID',
                    )
                ),
            ),
        ])

        # TODO

    """

    def __init__(
        self, 
        maxlen: int | None = None,
        event_ref: Event.Ref | None = None,
    ):
        r"""
        Initialize a new instance of :class:`VariableLogger`.
        
        :param maxlen: The maximum number of values to store.
            If not provided or `None`, all values are stored.
        :param event_ref: The event reference to trigger polling.
            If not provided or `None`, polling is manual.
        """

        super().__init__()
        self._data: _collections_.defaultdict[
            _typing_.Hashable,
            _typing_.Deque[_typing_.Any],
        ] = _collections_.defaultdict(
            lambda: _collections_.deque(maxlen=maxlen)
        )
        self._event_ref = event_ref

    def __attach__(self, engine):
        super().__attach__(engine)

        if self._event_ref is not None:
            self._engine.events.on(
                self._event_ref, 
                lambda _, self=self: self.poll(),
            )

        return self

    def add(self, ref: str | BaseVariable.Ref | _typing_.Iterator) -> _typing_.Self:
        r"""
        Reserve a slot for a variable reference.
        This is optional as the logger will automatically 
        reserve a slot the first time the variable is logged.

        :param ref: The variable reference to log.
        """

        if isinstance(ref, (str, BaseVariable.Ref)):
            self._engine.variables.on(ref)
        elif isinstance(ref, _typing_.Iterator):
            pass
        else:
            raise TypeError(f'Unsupported reference: {ref}')
        self._data[ref]

        return self

    def poll(self) -> _typing_.Self:
        r"""
        Poll the variables and log their values.
        """

        for ref, data in self._data.items():
            value = None
            if isinstance(ref, (str, BaseVariable.Ref)):
                try: value = self._engine.variables.get(ref).value
                except _exceptions_.TemporaryUnavailableError: pass
            elif isinstance(ref, _typing_.Iterator):
                value = next(ref)
            else:
                raise TypeError(f'Unsupported reference: {ref}')
            data.append(value)

        return self
    
    def __getitem__(self, ref: str | BaseVariable.Ref | _typing_.Iterator):
        r"""
        Get the logged values for a variable reference.

        :param ref: The variable reference.
        """

        return self._data[ref]

    def plot(self, trace_specs: list[TraceSpec | _typing_.Tuple], **plotly_kwds):
        r"""
        Plot the logged values of the variables.

        :param trace_specs: The trace specifications. TODO
        :param plotly_kwds: Additional keyword arguments to pass to the plotly figure.
        """

        return FigureWidget(self, trace_specs, **plotly_kwds).update()
    
    # TODO 
    def dataframe(self):
        import pandas as _pandas_
        return _pandas_.DataFrame(self._data)
    

__all__ = [
    'VariableLogger',
]