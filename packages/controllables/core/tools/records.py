r"""
Record-keeping tools.

Scope: Runtime reference tracking and logging.
"""


import collections as _collections_
import functools as _functools_
from typing import (
    Any, 
)

from ..callbacks import BaseCallback, CallbackManager
from ..errors import OptionalModuleNotFoundError
from ..variables import BaseVariable, BaseVariableManager
from ..components import BaseComponent
from ..refs import deref, Derefable
from .plot import PlotConstructor


# TODO
class VariableRecord(
    BaseVariable, 
    BaseComponent[BaseVariable],
):
    r"""TODO"""

    def __init__(
        self,
        target: BaseVariable | None = None,
        maxlen: int | None = None,
    ):
        # TODO detach?
        if target is not None:
            self.__attach__(target)
        self._data = _collections_.deque(maxlen=maxlen)

    @_functools_.cached_property
    def events(self):
        return CallbackManager()

    @property
    def value(self):
        return self._data
    
    def poll(self):
        # TODO raise?
        if self._manager is None:
            return
        
        self._data.append(self._manager.value)
        self.events['change']()

        return self

    # TODO detach?
    def watch(self, event: BaseCallback | Derefable[BaseCallback] = 'change'):
        event = (
            event
            if isinstance(event, BaseCallback) else 
            deref(self._manager.events, event)
        )

        @event.on
        def _(*args, **kwargs):
            self.poll()

        return self
    

class VariableRecords(
    dict[Any, VariableRecord],
    BaseVariableManager[Any, VariableRecord],
):
    def __init__(
        self, 
        targets: dict[Any, BaseVariable], 
        maxlen: int | None = None,
    ):
        super().__init__({
            key: VariableRecord(
                target=target,
                maxlen=maxlen,
            )
            for key, target in targets.items()
        })

    @_functools_.cached_property
    def events(self):
        return CallbackManager()

    def poll(self):
        for record in self.values():
            record.poll()
        self.events['change']()
        return self
    
    def watch(self, event: BaseCallback):
        @event.on
        def _(*args, **kwargs):
            self.poll()
        return self

    # TODO
    @_functools_.cached_property
    def plot(self):
        r"""
        Plot the history.

        See :class:`Plot` for more information.
        """

        return PlotConstructor().__attach__(self)

    class DataFrameConstructor(BaseComponent['VariableRecords']):
        r"""
        The :class:`pandas.DataFrame` constructor.

        """

        def __call__(self, **kwargs):
            try:
                from pandas import DataFrame, Series
            except ModuleNotFoundError as e:
                raise OptionalModuleNotFoundError.suggest(['pandas']) from e

            # TODO unequal lengths
            return DataFrame({
                key: Series(record.value)
                for key, record in self._manager.items()
            }, **kwargs)
        
    @_functools_.cached_property
    def dataframe(self):
        r"""
        
        TODO autoupdate
        """

        return self.DataFrameConstructor().__attach__(self)


# TODO use VariableTable and row orientation!!!!
# TODO support for dataclass and namedtuple!!!?


__all__ = [
    'VariableRecord',
    'VariableRecords',
]