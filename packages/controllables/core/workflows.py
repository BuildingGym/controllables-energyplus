r"""
Workflows.

Scope: Workflow management for objects and functions.
"""


import functools as _functools_
import dataclasses as _dataclasses_
from typing import (
    Any,
    Generic,
    TypeVar,
    Literal,
    Callable,
)

from .callbacks import CallbackManager
from .components import BaseComponent


@_dataclasses_.dataclass
class Workflow(
    Generic[
        _RefT := TypeVar('_RefT'),
        _TargetT := TypeVar('_TargetT'),
    ],
):
    ref: _RefT
    target: _TargetT | None = None


class WorkflowManager(
    BaseComponent[_RefT := TypeVar('_RefT')],
    CallbackManager[
        _RefT,
        Callable[
            [Workflow[_RefT, _ManT := TypeVar('_ManT')]],
            Any,
        ],
    ],
    Generic[_RefT, _ManT],    
):
    def __call__(self, ref):
        return super().__call__(
            ref, 
            Workflow(ref=ref, target=self._manager),
        )
    

# TODO necesito?
import wrapt as _wrapt_

from .callbacks import CallbackManager

# TODO
class CallableObserver(_wrapt_.ObjectProxy):
    """
    TODO FIXME should __events__ be stored in the instance or the class?

    A wrapper that makes a function observable
    by emitting events before and after the function call.

    Examples:

    .. code-block:: python

        # TODO
        class Fun:
            @observable
            def play(self):
                print('haj', self.play.__events__)

        Fun().play()


    """

    # def __init__(self, func: Callable):
    #     self._func = func
    #     _functools_.update_wrapper(self, self._func)

    @_functools_.cached_property
    def __events__(self) -> CallbackManager[
        Literal['call:pre', 'call:post'],
        Callable,
    ]:
        return CallbackManager()
        
    def __call__(self, *args, **kwargs):
        self.__events__.__call__('call:pre', *args, **kwargs)
        res = self.__wrapped__(*args, **kwargs)
        self.__events__.__call__('call:post', *args, **kwargs)
        return res

    def __get__(self, instance, owner=None):
        import types as _types_
        return _types_.MethodType(self, instance) if instance is not None else self

# TODO FIXME
observable = CallableObserver


__all__ = [
    'Workflow',
    'WorkflowManager',
    #'CallableObserver',
    #'observable',
]