r"""
Plotting tools.

Scope: Plotting tools for visualizing realtime data.
"""


import abc as _abc_
from typing import (
    Any, 
    Iterable, 
    Mapping,
    Optional,
    Self,
    TypedDict,
    Unpack,
    Literal,
)

from ..callbacks import BaseCallback
from ..components import BaseComponent
from ..errors import OptionalModuleNotFoundError
from ..variables import BaseVariable, BaseVariableManager
from ..refs import Derefable, deref


class PlotSpec(TypedDict, total=False):
    r"""
    The plot specification.
    Plot refers to a single figure with traces.

    For available backends, see :attr:`Plot.backends`.
    """

    class Trace(TypedDict, total=False):
        r"""
        The trace specification.
        """

        kind: Optional[Literal['scatter']]
        r"""
        The trace kind. Supported options:
        * `scatter`: Scatter plot.
        """
        mode: Optional[Literal['lines', 'markers', 'lines+markers']]
        r"""
        The trace mode. Supported options:
        * `lines`: Lines.
        * `markers`: Markers.
        * `lines+markers`: Lines and markers.
        """        

        x: Optional[BaseVariable | Derefable[BaseVariable]]
        r"""The reference to x data."""
        y: Optional[BaseVariable | Derefable[BaseVariable]]
        r"""The reference to y data."""
        z: Optional[BaseVariable | Derefable[BaseVariable]]
        r"""The reference to z data."""

        label: Optional[Any]
        r"""The trace label to display."""
        backend_kwds: Optional[Mapping[str, Any]]
        r"""The backend keyword arguments for this trace."""

    traces: Optional[Iterable[Trace]]
    r"""The traces to plot."""

    backend: Optional[Literal['default'] | Any]
    r"""
    The backend to use for this plot. Supported options:
    * `default`: The default backend. Reserved.
    * Any other backend registered in :attr:`Plot.backends`.
    """
    backend_kwds: Optional[Mapping[str, Any]]
    r"""The backend keyword arguments."""


# TODO support for snapshots
class BasePlot(
    BaseComponent[BaseVariableManager], 
    _abc_.ABC,
):
    r"""
    Plot backend.
    
    """

    @_abc_.abstractmethod
    def __init__(self, spec: PlotSpec):
        r"""
        Create a plot per spec.

        :param spec: The plot specification.
        """

        ...

    @_abc_.abstractmethod
    def poll(self) -> Self:
        r"""
        Poll the plot.
        Implementation shall update the figure with 
        the latest data from the references.

        :returns: This plot.
        """

        ...

    def watch(self, event: BaseCallback) -> Self:
        # TODO !!!!!!
        @event.on
        def _(*args, **kwargs):
            self.poll()

        return self

    def _repr_mimebundle_(self, *args, **kwargs):
        r"""
        MIME bundle representation for rich display.
        
        .. seealso:: https://ipython.readthedocs.io/en/stable/config/integrating.html#rich-display
        """

        pass

    figure: Any | Self
    r"""
    The underlying figure object.
    This is implementation-specific.
    """


class Plot(BasePlot):
    r"""
    Plot.
    A single entry point for all backends 
    registered in :attr:`backends`.

    """

    backends = dict[Any, BasePlot]()

    @classmethod
    def backend(cls, name: Any):
        r"""
        Decorator for registering a backend.

        :param name: The backend name to use in :attr:`backends`.
        """

        def setter(v: BasePlot):
            cls.backends[name] = v
            return v
        return setter

    def __init__(self, spec):
        self._base: BasePlot = self.backends[
            spec.get('backend', 'default')
        ](spec)

    def __attach__(self, manager) -> Self:
        super().__attach__(manager)
        self._base.__attach__(self._manager)
        return self

    def poll(self):
        return self._base.poll()

    def watch(self, event):
        return self._base.watch(event)

    def _repr_mimebundle_(self, *args, **kwargs):
        return self._base._repr_mimebundle_(*args, **kwargs)
    
    @property
    def figure(self):
        return self._base.figure


# TODO BaseComponent for events


# TODO
class PlotConstructor(BaseComponent[BaseVariableManager]):
    # TODO !!!!!!
    def __watch__(self, event: BaseCallback):
        pass
    
    def __call__(self, spec):
        return Plot(spec=spec).__attach__(self._manager).poll()
    
    # TODO !!!!!
    def scatter(self, **trace_spec: Unpack[PlotSpec.Trace]):
        return self.__call__({
            'traces': [{
                'kind': 'scatter',
                **trace_spec,
            }],
        })
    
plot = PlotConstructor()


@Plot.backend('default')
@Plot.backend('plotly')
class PlotlyBackend(BasePlot):
    r"""
    Plotly plot.

    TODO backend_kwds

    """

    def __init__(self, spec):
        try:
            from plotly.graph_objects import FigureWidget # Figure
        except ModuleNotFoundError as e:
            raise OptionalModuleNotFoundError.suggest(['plotly']) from e

        self._spec = spec

        self._figure = FigureWidget(
            **self._spec.get('backend_kwds', dict()),
        )
        for trace_spec in self._spec.get('traces', []):
            match trace_spec.get('kind', 'scatter'):
                case 'scatter':
                    self._figure.add_trace({
                        'type': 
                            'scatter3d' 
                            if 'z' in trace_spec else 
                            'scatter',
                        'name': trace_spec.get('label'),
                        # TODO
                        'mode': trace_spec.get('mode'),
                        **trace_spec.get('backend_kwds', dict()),
                    })
                case _:
                    raise ValueError(
                        f'''Unsupported trace kind: {trace_spec.get('kind')}. See {PlotSpec.Trace}'''
                    )

    def poll(self):
        def _deref(ref: BaseVariable | Derefable[BaseVariable]):
            return (
                ref 
                if isinstance(ref, BaseVariable) else 
                deref(self._manager, ref)
            )

        def _ensure_data(data: Iterable | Any):
            return list(data) if isinstance(data, Iterable) else data

        self._figure.update({
            'data': [
                {
                    prop: _ensure_data(
                        _deref(trace_spec.get(ref_prop)).value
                    )
                    for prop, ref_prop in [
                        ('x', 'x'),
                        ('y', 'y'),
                        ('z', 'z'),
                    ]
                    if ref_prop in trace_spec
                } for trace_spec in self._spec['traces']
            ],
        })

        return self

    def _repr_mimebundle_(self, *args, **kwargs):
        return self._figure._repr_mimebundle_(*args, **kwargs)
    
    @property
    def figure(self):
        return self._figure


@Plot.backend('_TODO_mpl')
class MatplotlibBackend(BasePlot):
    r"""
    Matplotlib plot.

    """

    def __init__(self, spec):
        try:
            from matplotlib.figure import Figure
            from matplotlib.axes import Axes
        except ModuleNotFoundError as e:
            raise OptionalModuleNotFoundError.suggest(['matplotlib']) from e

        self._spec = spec

        self._figure = Figure(
            **self._spec.get('backend_kwds', dict()),
        )
        #self._figure.subplots()

        self._figure.add_artist
        self._figure.add_axes

        raise NotImplementedError

    def poll(self):
        #self._figure.artists
        
        raise NotImplementedError
    
        _deref = lambda x: deref(self._manager, x)

        for trace_spec in self._spec.get('traces', []):
            if trace_spec.get('kind') == 'scatter':
                x = _deref(trace_spec.get('x')).value
                y = _deref(trace_spec.get('y')).value
                self._axes.collections.clear()
                self._axes.scatter(x, y)

        return self

    def _repr_mimebundle_(self, *args, **kwargs):
        raise NotImplementedError

        return self._figure._repr_mimebundle_(*args, **kwargs)
    
    @property
    def figure(self):
        return self._figure


__all__ = [
    'PlotSpec',
    'BasePlot',
    'Plot',
    'PlotConstructor',
    'plot',
]