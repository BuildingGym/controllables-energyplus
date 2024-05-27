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
    r"""The main simulation engine."""

    class State(_enum_.Enum):
        IDLE = 0
        RUNNING = 1
        STOPPING = 2

    class InputSpecs(_typing_.NamedTuple):
        model: _datas_.InputModel | _os_.PathLike
        weather: _datas_.WeatherModel | _os_.PathLike | None = None

    class OutputSpecs(_typing_.NamedTuple):
        # TODO mv to runtimeopts?
        report: _datas_.Report | _os_.PathLike | None = None

    class RuntimeOptions(_typing_.NamedTuple):
        recurring: bool = False
        design_day: bool = False

    def __init__(
        self, 
        input: InputSpecs | dict, 
        output: OutputSpecs | dict = OutputSpecs(),
        options: RuntimeOptions | dict = RuntimeOptions(),
    ):
        def build(
            typ: '_typing_.Type[_typing_.NamedTuple]',
            obj: '_typing_.NamedTuple | dict', 
        ):
            return typ(**(
                obj._asdict() if isinstance(obj, typ) else obj
            ))
        
        self._input = build(Engine.InputSpecs, input)
        self._output = build(Engine.OutputSpecs, output)
        self._options = build(Engine.RuntimeOptions, options)

    _input: InputSpecs
    _output: OutputSpecs
    _options: RuntimeOptions
    
    _state: State = State.IDLE

    @_functools_.cached_property
    def _workflows(self):
        return WorkflowManager()

    @_functools_.cached_property
    def _core(self):
        return _core_.Core()

    def run(self):
        r"""Run the engine."""

        if self._state != Engine.State.IDLE:
            raise RuntimeError('Engine is already running.')

        input, output, options = self._input, self._output, self._options

        while self._state != Engine.State.STOPPING:
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
                            input.model.dumpf(
                                _tempfile_.NamedTemporaryFile(suffix='.epJSON').name,
                                format='json',
                            ) 
                            if isinstance(input.model, _datas_.InputModel) else
                            _pathlib_.Path(input.model)
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
            self._state = Engine.State.IDLE
            if status != 0:
                raise RuntimeError(f'Operation failed with status {status}.')
            self._workflows.trigger(Workflow('run:post', self))

            if not options.recurring:
                break

    def stop(self):
        r"""Stop the engine."""
        
        self._workflows.trigger(Workflow('stop:pre', self))
        self._state = Engine.State.STOPPING
        self._core.api.runtime \
            .stop_simulation(self._core.state)
        self._workflows.trigger(Workflow('stop:post', self))

    # TODO
    def add(self, *components: '_base_.Component'):
        for component in components:
            component.__attach__(self)
        return self
    
    # TODO
    def remove(self, *components: '_base_.Component'):
        raise NotImplementedError
        return self
    

class AsyncEngineController(_base_.Component):
    def run(self, *args, **kwargs):
        return _asyncio_.create_task(
            _utils_.awaitables.asyncify()
            (self._engine.run)(*args, **kwargs)
        )

    def stop(self, *args, **kwargs):
        return _asyncio_.create_task(
            _utils_.awaitables.asyncify()
            (self._engine.stop)(*args, **kwargs)
        )


class World(Engine):
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


__all__ = [
    'Engine',
    'AsyncEngineController',
    'World',
]
