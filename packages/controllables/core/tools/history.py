r"""
Record-keeping tools.

Scope: Runtime reference tracking and logging.
"""


import abc as _abc_
import collections as _collections_
import dataclasses as _dataclasses_
import functools as _functools_
from typing import (
    Any, 
    Iterator,
    Optional,
    TypedDict,
    Generic,
    TypeVar,
    Literal,
)


from ..specs.callbacks import BaseCallback
from ..specs.variables import BaseVariable
from ..specs.components import BaseComponent
from ..specs.workflows import WorkflowManager
from ..specs.refs import RefManager
from .plot import PlotSpec, Plot


class History(
    RefManager,
    _abc_.ABC,
    Generic[
        _RefT := TypeVar('_RefT'),
    ],
):
    r"""
    History.
    
    Examples:

    .. code-block:: python

        # TODO
        world = ...
        env = ...

        history = History() \
            # make 'clk' an alias for `world['wallclock:calendar']`
            .track('clk', world['wallclock:calendar'])

        history.plot(
            # specify the plot spec
            {
                'traces': [{
                    'x': 'clk', 
                    # `world['wallclock']` is now tracked
                    'y': world['wallclock'],
                    # `env.reward` is now tracked
                    'z': env.reward,
                }],
            }, 
            # update this plot every 1k update cycles
            autoupdate=1_000,
        )

        # initiate one update cycle
        history.poll()

    """

    @_functools_.cached_property
    def workflows(self):
        return WorkflowManager[
            Literal['poll'],
            History,
        ]().__attach__(self)
    
    class Spec(TypedDict):
        maxlen: Optional[int]
        
    @_dataclasses_.dataclass
    class Record:
        ref: _RefT
        # TODO make this a BaseVariable
        values: _collections_.deque

    def __init__(
        self, 
        spec: Spec | None = None, 
        refs: RefManager[_RefT] | None = None,
    ):
        r"""
        Initialize this history instance.

        :param spec: The history spec.
        :param refs: The reference manager.
        """

        self._spec = spec if spec is not None else self.Spec()
        self._refs = refs
        self._data = dict[Any, self.Record]()
        
    def __contains__(self, key: Any):
        return key in self._data

    def __getitem__(self, key: Any):
        if key not in self:
            self.track(key)
        return self._data[key].values
    
    def keys(self):
        return self._data.keys()

    def track(self, key: Any, ref: _RefT | None = None):
        r"""
        Track a reference.
        Normally it is not necessary to call this method explicitly
        as the reference will be tracked automatically when accessed.
        
        :param key: The key to use as reference for :param:`ref`.
        :param ref: The reference to track. If not provided, the key will be used.
        """

        self._data[key] = self.Record(
            ref=ref if ref is not None else key,
            values=_collections_.deque(
                maxlen=self._spec.get('maxlen')
            ),
        )

    def poll(self):
        r"""
        Poll the references and log the values.
        This counts as one update cycle.

        :returns: This logger instance.
        """

        if self._refs is None:
            return self

        for _, record in self._data.items():
            # TODO
            record.values.append(self._refs[record.ref])

        self.workflows.__call__('poll')

        return self
    
    class Plot(Plot, BaseComponent['History']):
        r"""
        The plot component for :class:`History`s.

        """

        def __init__(
            self, 
            spec: PlotSpec, 
            refs: RefManager | None = None,
            autoupdate: bool | int = False,
        ):
            r"""
            Initialize a plot.

            :param autoupdate: 
                Update the plot when the :meth:`__attach__`-ed 
                :class:`History` is `poll`ed.
                * If :class:`bool`, specifies whether to auto-update the plot.
                * If :class:`int`, specifies the auto-update frequency.
            """

            super().__init__(spec=spec, refs=refs)
            self._autoupdate = autoupdate

        def __attach__(self, manager):
            super().__attach__(manager)

            if self._autoupdate:
                workflows = self._manager.workflows['poll']
                if isinstance(self._autoupdate, int):
                    workflows = workflows.sample.uniform(self._autoupdate)
                workflows.on(lambda _: self.poll())

            return self
        
    def plot(self, spec: PlotSpec, autoupdate: bool | int = False):
        r"""
        Plot the history.

        See :class:`Plot` for more information.
        """

        return self.Plot(
            spec=spec, 
            refs=self, 
            autoupdate=autoupdate,
        ).__attach__(self)
    
    class DataFrameConstructor(BaseComponent['History']):
        r"""
        The :class:`pandas.DataFrame` constructor.

        """

        def __call__(self, **kwargs):
            import pandas as _pandas_
            return _pandas_.DataFrame({
                key: self._manager[key]
                for key in self._manager.keys()
            }, **kwargs)
        
    @_functools_.cached_property
    def dataframe(self):
        r"""
        
        TODO autoupdate
        """

        return self.DataFrameConstructor().__attach__(self)


from ..specs.variables import BaseVariable, VariableRefManager

# TODO
class VariableHistory(
    History[None | BaseVariable | Iterator],
):
    # TODO errors: 'ignore' | 'raise' | 'warn'
    def __init__(
        self, 
        spec=None, 
        refs=VariableRefManager(),
    ):
        super().__init__(spec, refs)


__all__ = [
    'History',
    'VariableHistory',
]



# TODO
class Record(BaseVariable):
    r"""TODO"""

    # TODO stdize in BaseVariable
    @_functools_.cached_property
    def workflows(self):
        return WorkflowManager[
            Literal['change'],
            History,
        ]().__attach__(self)
    
    def __init__(
        self, 
        ref: BaseVariable, 
        maxlen: int | None = None,
        # TODO
        update: BaseCallback | Any | None = None,
    ):
        super().__init__()
        self._ref = ref
        self._data = _collections_.deque(maxlen=maxlen)
        
    @property
    def value(self):
        return self._data
    
    @property
    def ref(self):
        return self._ref

    def poll(self):
        self._data.append(self._ref.value)
        self.workflows.__call__('change')


# TODO events
class RecordManager:
    @_functools_.cached_property
    def _data(self):
        return dict[Any, Record]()
    
    @_functools_.cached_property
    def workflows(self):
        return WorkflowManager[
            Literal['change'],
            RecordManager,
        ]().__attach__(self)
    
    def __init__(self, maxlen: int = None):
        self._maxlen = maxlen
        
    def __contains__(self, key: Any):
        return key in self._data

    def __getitem__(self, key: Any):
        if key not in self:
            self.track(key)
        return self._data[key]
    
    def track(self, key: Any, ref: Any | None = None):
        r"""
        Track a reference.
        It is not necessary to call this method explicitly
        as the reference will be tracked automatically when accessed.
        
        :param key: The key to use to access the record of :param:`ref`.
        :param ref: The reference to track. If not provided, the key will be used.
        """

        self._data[key] = Record(
            ref=ref if ref is not None else key,
            maxlen=self._maxlen,
        )

    def poll(self):
        r"""
        Poll the references and log the values to respective records.
        This counts as one update cycle.
        """

        for _, record in self._data.items():
            record.poll()
        self.workflows.__call__('change')


__all__ = [
    'Record',
    'RecordManager',
]