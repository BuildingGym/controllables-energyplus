# TODO variable viz
from .. import base as _base_

import typing as _typing_
from ... import (
    components as _components_,
)



class VariableVisualizer(_base_.Addon):
    # TODO
    class Config:
        variable_refs: _typing_.Iterable[_components_.variables.BaseVariable.Ref]
        event_refs: ...

    # TODO x, y, z, w
    def __init__(self, variable_refs):
        super().__init__()

    def __attach__(self, engine):
        # TODO
        super().__attach__(engine=engine)
        raise NotImplementedError
        return self
    
    def _TODO_step(self):
        pass

# TODO TrendVisualizer

# TODO mpl svg animations https://github.com/matplotlib/matplotlib/issues/19694

# TODO animation and figure


__all__ = [
    VariableVisualizer,
]