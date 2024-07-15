r"""
Plotting tools.

Scope: Plotting tools for visualizing reference data.
"""


import abc as _abc_
from typing import (
    Any, 
    Iterable, 
    Mapping,
    Optional,
    Self,
    TypedDict,
    Generic,
    TypeVar,
    Literal,
)


class PlotSpec(
    TypedDict,
    Generic[_RefT := TypeVar('_RefT')],
    total=False,
):
    r"""
    The plot specification.
    Plot refers to a single figure with traces.

    For available backends, see :attr:`Plot.backends`.
    """

    class Trace(TypedDict, total=False):
        r"""
        The trace specification.
        """

        x: Optional[_RefT]
        r"""The reference for x data."""
        y: Optional[_RefT]
        r"""The reference for y data."""
        z: Optional[_RefT]
        r"""The reference for z data."""
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


from ..refs import RefManager


# TODO
class BasePlot(_abc_.ABC):
    r"""
    Plot backend.
    
    """

    @_abc_.abstractmethod
    def __init__(self, spec: PlotSpec, refs: RefManager | None = None):
        r"""
        Create a plot per spec.

        :param spec: The plot spec.
        :param refs: The reference manager.
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

    def _repr_mimebundle_(self, *args, **kwargs):
        r"""
        MIME bundle representation for rich display.
        
        .. seealso:: https://ipython.readthedocs.io/en/stable/config/integrating.html#rich-display
        """

        ...


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
    
    def __init__(self, spec, refs=None):
        self._base: BasePlot = self.backends[
            spec.get('backend', 'default')
        ](spec, refs)
        
    def poll(self):
        return self._base.poll()
    
    def _repr_mimebundle_(self, *args, **kwargs):
        return self._base._repr_mimebundle_(*args, **kwargs)


# TODO
class PlotConstructor:
    def __call__(self, spec, refs=None):
        return Plot(spec, refs)
    
    # TODO
    def scatter(self, x, y, z):
        pass


@Plot.backend('default')
@Plot.backend('plotly')
class PlotlyBackend(BasePlot):
    r"""
    Plotly plot.

    TODO backend_kwds

    """

    def __init__(self, spec, refs=None):
        self._spec = spec
        self._refs = refs

        from plotly.graph_objects import FigureWidget
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
                        f'''Unsupported trace kind: {trace_spec.get('kind')}'''
                    )

    def poll(self):
        if self._refs is None:
            return self

        self._figure.update({
            'data': [
                {
                    prop: list(self._refs[trace_spec.get(ref_prop)])
                    for prop, ref_prop in [
                        ('x', 'x'),
                        ('y', 'y'),
                        ('z', 'z'),
                    ]
                    if ref_prop in trace_spec
                }
                for trace_spec in self._spec['traces']
            ],
        })

        return self

    def _repr_mimebundle_(self, *args, **kwargs):
        return self._figure._repr_mimebundle_(*args, **kwargs)


@Plot.backend('_TODO_mpl')
class MatplotlibBackend(BasePlot):
    r"""
    Matplotlib plot.

    """

    def __init__(self, spec, refs=None):
        self._spec = spec
        self._refs = refs

        from matplotlib.figure import Figure
        self._figure = Figure(
            **self._spec.get('backend_kwds', dict()),
        )
        #self._figure.subplots()

        from matplotlib.axes import Axes


        self._figure.add_artist
        self._figure.add_axes

        raise NotImplementedError


    def poll(self):
        if self._refs is None:
            return self
        
        #self._figure.artists
        
        raise NotImplementedError

        for trace_spec in self._spec.get('traces', []):
            if trace_spec.get('kind') == 'scatter':
                x = self._refs[trace_spec.get('x')]
                y = self._refs[trace_spec.get('y')]
                self._axes.collections.clear()
                self._axes.scatter(x, y)

        return self

    def _repr_mimebundle_(self, *args, **kwargs):
        raise NotImplementedError

        return self._figure._repr_mimebundle_(*args, **kwargs)


__all__ = [
    'PlotSpec',
    'Plot',
]
