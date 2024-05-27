
import numpy as _numpy_

class CoordinateView:
    def __init__(self, ndim):
        self._ndim = ndim

    def dtype(self, base=object):
        res_full = [('x', base), ('y', base), ('z', base)]
        if self._ndim > len(res_full):
            raise ValueError(f'ndim {self._ndim} greater than accepted maximum {res_full}.')
        return res_full[:self._ndim]

    def cast(self, arr, base_dtype=object, *np_args, **np_kwargs):
        return _numpy_.array(
            arr, self.dtype(base=base_dtype), 
            *np_args, **np_kwargs,
        )

    def map(self, arr, func, base_dtype=object):
        r"""
        Apply function `func` to every item of `arr`
        # TODO doc apply transformation func to each element of the coordinate system array
        """
        return self.cast([
            tuple(func(element) for element in row)
            for row in self.cast(arr, ndmin=1, base_dtype=object)
        ], base_dtype=base_dtype)
        

class Test_CoordinateView:
    def test_TODO(self):
        # TODO mv
        _numpy_.testing.assert_array_equal(
            CoordinateView(ndim=2).map(
                [(2, 3)],
                lambda x: x**2,
                base_dtype=object,
            ),
            _numpy_.array([(4., 9.)], dtype=[('x', '<f8'), ('y', '<f8')])    
        )


import numpy as _numpy_

import matplotlib as _matplotlib_
import matplotlib.lines



class Line2DView:
    def __init__(self, obj: _matplotlib_.lines.Line2D):
        self._obj = obj

    def _ensure_struct(self, arr):
        # TODO doc accepted value: [(1, 2), (3, 4)] or (1, 2)
        return CoordinateView(ndim=2).cast(arr, ndmin=1)

    @property
    def value(self):
        # TODO doc
        """Get the line data as a structured numpy array."""
        xdata, ydata = self._obj.get_data()
        return self._ensure_struct(
            list(zip(xdata, ydata)),
        )

    @value.setter
    def value(self, value):
        # TODO doc, typing
        """Set the line data from a structured numpy array."""
        value = self._ensure_struct(value)
        self._obj.set_data(
            *([value[field] for field in value.dtype.fields])
        )

    def extend(self, value):
        # TODO doc, typingtyping
        """Extend the line with more points."""
        value = self._ensure_struct(value)
        self.value = _numpy_.concatenate(
            (self.value, value), 
            #axis=0,
        )
        return self

    def clip(self, size):
        self.value = self.value[size:]
        return self

    def ensure_unique(self, key):
        _, indices = _numpy_.unique(self.value[key], return_index=True)
        self.value = self.value[indices]
        return self


import typing as _typing_
import operator as _operator_

import matplotlib as _matplotlib_

# TODO fill in the relevant typing info from matplotlib
class BaseArtistProvider:
    artist: '_matplotlib_.artist.Artist'

    def draws_on(self, ax_or_fig: _typing_.Union['_matplotlib_.axes.Axes', '_matplotlib_.figure.Figure']):
        ax_or_fig.add_artist(self.artist)
        return self

# TODO thread safe
class Line2DProvider(BaseArtistProvider):
    def __init__(
        self, 
        # TODO complete doc and type hints:
        # TODO () -> (x[], y[])
        # TODO (() -> (x), () -> (y))
        # TODO [() -> (x), () -> (y)]
        data_ref: callable,
        update_method: _typing_.Literal['set', 'extend'] = 'extend',
        **mpl_kwargs,
    ):
        self.update_method = update_method
        if isinstance(data_ref, _typing_.Callable):
            self.data_gen = data_ref
        else:
            self.data_gen = lambda data_ref=data_ref: (
                CoordinateView(ndim=2)
                .map(
                    data_ref, _operator_.call, 
                    base_dtype=object,
                )
            )
        self.artist = _matplotlib_.lines.Line2D([], [], **mpl_kwargs)

    def update(self):
        view = Line2DView(self.artist)

        match self.update_method:
            case 'set':
                view.value = self.data_gen()
            case 'extend':
                view.extend(self.data_gen())
            case _:
                raise ValueError(rf'Unknown update method {self.update_method}')

        return self

# TODO mv
class Test_Line2DProvider:
    def test_TODO(self):
        import matplotlib.pyplot as _plt_
        import numpy as _numpy_

        _, ax = _plt_.subplots()

        line_provider = Line2DProvider(
            (lambda: _numpy_.random.rand(), lambda: _numpy_.random.rand()),
            update_method='extend',
        ).draws_on(ax)

        for _ in range(100):
            line_provider.update()


import typing as _typing_
import matplotlib.pyplot


class LineChart2DProvider:
    # TODO typing
    def __init__(
        self, 
        line_factory: _typing_.Callable[[], Line2DProvider] = Line2DProvider,
        autoview: bool = True,
        # TODO !!!!!!!!!!!!!!!
        uniques: list[str | _typing_.Literal['x', 'y']] = ['x'],
    ):
        self.uniques = uniques
        self.autoview = autoview
        self.line_factory = line_factory
        self.lines: list[Line2DProvider] = []
        self.figure, self.ax = _matplotlib_.pyplot.subplots()

    def add(self, *args, **kwargs):
        self.lines.append(
            self.line_factory(*args, **kwargs)
                .draws_on(self.ax)
        )
        return self
    
    def update(self):
        # TODO
        for line in self.lines: 
            line.update()
            # TODO mv !!!!!!!!!!!!!
            Line2DView(line.artist).clip(-500)
            for key in self.uniques:
                Line2DView(line.artist).ensure_unique(key=key)
        
        if self.autoview:
            self.ax.relim()
            self.ax.autoscale_view()
        self.figure.canvas.draw_idle()
        
        return self
    
    def legend(self, *args, **kwargs):
        self.ax.legend(*args, **kwargs)
        return self