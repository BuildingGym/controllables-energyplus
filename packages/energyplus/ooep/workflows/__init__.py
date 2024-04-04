import typing as _typing_
import dataclasses as _dataclasses_

from .. import (
    utils as _utils_,
    engines as _engines_,
)

@_dataclasses_.dataclass
class Workflow(_utils_.events.BaseEvent):    
    ref: str
    # TODO
    engine: '_engines_.simulators.Simulator'

class WorkflowManager(
    _utils_.events.BaseEventManager, 
):
    # TODO
    def available_keys(self):
        return [
            'run:pre', 
            'run:post',
            'stop:pre', 
            'stop:post',
            'reset:pre', 
            'reset:post',
        ]
    
__all__ = [
    Workflow,
    WorkflowManager,
]
