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
    raise _base_.OptionalImportError.suggest(['plotly']) from e


class VariableLogger(_base_.Addon):
    r"""
    A logger that logs variable values over time.

    Example usage:

    .. code-block:: python
        world = ...

        VariableLogger() \
            .__attach__(world)
            .add('wallclock') \
            .add(iter(range(10)))
        
        VariableLogger(maxlen=100) \
            .__attach__(world)
            .plot([
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
        VariableLogger(maxlen=100) \
            .__attach__(world)
            .dataframe()
    """

    def __init__(
        self, 
        maxlen: int | None = None,
        event_ref: Event.Ref | None = None,
    ):
        r"""
        Initialize a new instance of :class:`VariableLogger`.
        
        :param maxlen: 
            The maximum number of values to store.
            If not provided or `None`, all values are stored.
        :param event_ref: 
            The event reference to trigger polling (log operation).
            If not provided or `None`, polling is manual. 
            .. seealso:: :meth:`poll`
        """

        super().__init__()
        self._data: _collections_.defaultdict[
            _typing_.Hashable,
            _typing_.Deque[_typing_.Any],
        ] = _collections_.defaultdict(
            lambda: _collections_.deque(maxlen=maxlen)
        )
        self._event_ref = event_ref

        # TODO event manager

    def __attach__(self, engine):
        super().__attach__(engine)

        if self._event_ref is not None:
            self._engine.events.on(
                self._event_ref, 
                lambda _, self=self: self.poll(),
            )

        return self

    def add(
        self, 
        ref: str | BaseVariable.Ref | _typing_.Iterator,
    ) -> _typing_.Self:
        r"""
        Reserve a slot for a reference.
        This is optional as the logger will automatically 
        reserve a slot the first time a reference is accessed.

        :param ref: The reference to log.
        :returns: This logger instance.
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
        Poll the references and add their values to the log.
        * For variables, this logs the variable value;
        * For iterators, this logs the next value from the iterator.

        :returns: This logger instance.
        """

        # TODO
        for ref, data in self._data.copy().items():
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
        Get the logged historical values of a reference.

        :param ref: The reference.
        :returns: The logged values.
        """

        return self._data.__getitem__(ref)
    
    class Figure:
        class TraceSpec(_typing_.TypedDict):
            bindings: dict[
                str, 
                str | BaseVariable.Ref
                | _typing_.Iterator,
            ]

        def __init__(
            self, 
            logger: 'VariableLogger',
            trace_specs: list[TraceSpec | _typing_.Tuple], 
            **plotly_kwds,
        ):
            self._base = _plotly_.graph_objs.FigureWidget(
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

        @property
        def figure(self):
            return self._base

        def poll(self):
            r"""
            Poll the figure widget.
            This updates the figure contents with 
            the latest data from the logger.

            :returns: This figure widget.
            """
            with self._base.batch_update():
                for i, trace in enumerate(self._base.data):
                    for prop, ref in self._bindings[i].items():
                        trace[prop] = list(self._logger[ref])
            
            return self
        
        def _repr_mimebundle_(self, *args, **kwargs):
            return self._base._repr_mimebundle_(*args, **kwargs)

    def plot(self, trace_specs, **plotly_kwds) -> Figure:
        r"""
        Plot the logged historical values of references.

        :param trace_specs: The trace specifications. TODO
        :param plotly_kwds: Additional keyword arguments to pass to the plotly figure.
        :returns: A plotly figure widget.
        """

        return self.Figure(self, trace_specs, **plotly_kwds).poll()
    
    # TODO data, index, columns    
    def dataframe(self, **pandas_kwds):
        import pandas as _pandas_
        return _pandas_.DataFrame(self._data, **pandas_kwds)
    
    # TODO save, restore

__all__ = [
    'VariableLogger',
]