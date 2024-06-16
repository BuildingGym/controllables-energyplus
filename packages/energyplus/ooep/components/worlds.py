r"""
Worlds.

Scope: Engines and worlds.
"""

import typing as _typing_
import functools as _functools_
import dataclasses as _dataclasses_
import asyncio as _asyncio_
import os as _os_
import tempfile as _tempfile_
import pathlib as _pathlib_

from . import base as _base_
from .. import (
    _core as _core_,
    datas as _datas_,
    utils as _utils_,
)


@_dataclasses_.dataclass
class Workflow(_utils_.events.BaseEvent):    
    ref: str
    # TODO
    engine: 'Engine'

class WorkflowManager(
    _utils_.events.BaseEventManager, 
):
    # TODO
    def keys(self):
        return [
            'run:pre', 
            'run:post',
            'stop:pre', 
            'stop:post',
        ]


import enum as _enum_

# TODO subsimulation/namespacing
# TODO AddonManager?
class Engine(_base_.ComponentManager):
    r"""
    The main simulation engine.

    Example usage:

    .. code-block:: python
        # TODO

    """

    class State(_enum_.Enum):
        r"""
        The state of the engine.

        :cvar IDLE: The engine is idle.
        :cvar RUNNING: The engine is running.
        :cvar STOPPING: The engine is stopping.
        """
        IDLE = 0
        RUNNING = 1
        STOPPING = 2

    class Specs(_typing_.NamedTuple):
        r"""
        Specifications for the engine.

        :param input: The input specifications.
        :param output: The output specifications.
        :param runtime: The runtime specifications.     
        """

        class Input(_typing_.NamedTuple):
            r"""
            The input specifications.

            :param input: The input model.
            :param weather: The weather model.
            """
            input: _datas_.InputModel | _os_.PathLike
            weather: _datas_.WeatherModel | _os_.PathLike | None = None

        class Output(_typing_.NamedTuple):
            r"""
            The output specifications.

            :param report: The report.
            """
            report: _datas_.Report | _os_.PathLike | None = None

        class Runtime(_typing_.NamedTuple):
            r"""
            The runtime specifications.
            This controls the runtime behavior of the engine.

            :param recurring: Whether to run in a loop. 
                If `True`, the engine will run in a loop 
                until :meth:`stop` is called. 
                TODO max n epoches/runs.
            :param design_day: Whether to run in design day mode.
                ..seealso:: https://energyplus.readthedocs.io/en/latest/tips_and_tricks/tips_and_tricks.html#design-day-creation
            """
            recurring: bool = False
            design_day: bool = False

        input: Input
        output: Output
        runtime: Runtime

        @classmethod
        def make(
            cls,
            input: Input | dict, 
            output: Output | dict = dict(),
            runtime: Runtime | dict = dict(),
        ):
            r"""
            Make a new instance of :class:`Engine.Specs`.
            """
            def build(
                typ: '_typing_.Type[_typing_.NamedTuple]',
                obj: '_typing_.NamedTuple | dict', 
            ):
                return typ(**(
                    obj._asdict() if isinstance(obj, typ) else obj
                ))
            
            return cls(
                input=build(cls.Input, input),
                output=build(cls.Output, output),
                runtime=build(cls.Runtime, runtime),
            )

    def __init__(self, **specs: 'Engine.Specs'):
        r"""
        Initialize a new instance of :class:`Engine`.

        :param specs: The specifications of the engine. 
            ..seealso:: :meth:`Engine.Specs.make`.
        """
        self._specs = Engine.Specs.make(**specs)
    
    # TODO
    def __getstate__(self) -> Specs:
        r"""
        Pickle.

        :return: The specifications.

        .. note::
            Components are not pickled for now.       
        """
        return self._specs
    
    def __setstate__(self, specs: Specs):
        r"""
        Pickle.

        :param specs: The specifications.
        """
        self.__init__(**specs._asdict())

    _state: State = State.IDLE

    @_functools_.cached_property
    def _workflows(self):
        return WorkflowManager()

    @_functools_.cached_property
    def _core(self):
        return _core_.Core()

    def run(self):
        r"""
        Run the engine.
        
        :return: This engine.
        :raises RuntimeError: If the engine is already running.
        """

        if self._state != Engine.State.IDLE:
            raise RuntimeError(f'Engine is currently running: {self._state}.')

        input, output, options = (
            self._specs.input, 
            self._specs.output, 
            self._specs.runtime,
        )

        keepalive = True

        while keepalive:
            # NOTE state must be reset between runs
            self._core.reset()

            self._core.api.runtime \
                .set_console_output_status(
                    self._core.state,
                    print_output=False,
                )
            
            self._workflows.trigger(Workflow('run:pre', self))
            self._state = Engine.State.RUNNING
            status = self._core.api.runtime \
                .run_energyplus(
                    self._core.state,
                    command_line_args=[
                        str(
                            input.input.dumpf(
                                _tempfile_.NamedTemporaryFile(suffix='.epJSON').name,
                                format='json',
                            ) 
                            if isinstance(input.input, _datas_.InputModel) else
                            _pathlib_.Path(input.input)
                        ),
                        *(['--weather', str(
                            input.weather.path
                            if isinstance(input.weather, _datas_.WeatherModel) else
                            input.weather
                        )] if input.weather is not None else []),
                        '--output-directory', str(
                            output.report.path
                            if isinstance(output.report, _datas_.Report) else 
                            output.report
                            if output.report is not None else 
                            _tempfile_.TemporaryDirectory(
                                prefix='.energyplus_output_',
                            ).name
                        ),
                        *(['--design-day'] if options.design_day else []),
                    ],
                )
            if (self._state == Engine.State.STOPPING 
                    or not options.recurring):
                keepalive = False
            self._state = Engine.State.IDLE
            if status != 0:
                raise RuntimeError(f'Operation failed with status {status}.')
            self._workflows.trigger(Workflow('run:post', self))

        return self

    def stop(self):
        r"""
        Stop the engine.

        :return: This engine.
        :raises RuntimeError: If the engine is not running.
        """

        if self._state == Engine.State.IDLE:
            raise RuntimeError(f'Engine is not running: {self._state}.')

        self._workflows.trigger(Workflow('stop:pre', self))
        self._state = Engine.State.STOPPING
        self._core.api.runtime \
            .stop_simulation(self._core.state)
        self._workflows.trigger(Workflow('stop:post', self))

        return self

    # TODO deprecate??
    def add(self, *components: '_base_.Component'):
        for component in components:
            component.__attach__(self)
        return self
    
    # TODO
    def remove(self, *components: '_base_.Component'):
        raise NotImplementedError
        return self

class AsyncEngineController(_base_.Component):
    r"""
    An asynchronous controller for the engine.
    """

    def run(self, *args, **kwargs):
        r"""
        Run the engine asynchronously.
        """
        return _asyncio_.create_task(
            _utils_.awaitables.asyncify()
            (self._engine.run)(*args, **kwargs)
        )

    def stop(self, *args, **kwargs):
        r"""
        Stop the engine asynchronously.
        """
        return _asyncio_.create_task(
            _utils_.awaitables.asyncify()
            (self._engine.stop)(*args, **kwargs)
        )


class World(Engine):
    r"""
    TODO
    """

    @_functools_.cached_property
    def events(self):
        from .events import EventManager
        return EventManager().__attach__(self)
    
    @_functools_.cached_property
    def variables(self):
        from .variables import VariableManager
        return VariableManager().__attach__(self)
    
    @_functools_.cached_property
    def awaitable(self):
        return AsyncEngineController().__attach__(self)
    
    def __getstate__(self) -> Engine.Specs:
        return super().__getstate__()
    
    def __setstate__(self, specs: Engine.Specs):
        return super().__setstate__(specs)


__all__ = [
    'Engine',
    'AsyncEngineController',
    'World',
]
