# TODO variable viz
from .. import base as _base_


class VariableVisualizer(_base_.Addon):
    # TODO x, y, z, w
    def __init__(self, variable_keys):
        super().__init__()

    def __attach__(self, engine):
        # TODO
        super().__attach__(engine=engine)
        raise NotImplementedError
        return self
    
__all__ = [
    VariableVisualizer,
]