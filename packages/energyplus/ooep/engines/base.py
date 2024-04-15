from __future__ import annotations

import abc as _abc_
import typing as _typing_


import typing as _typing_
import functools as _functools_
import tempfile as _tempfile_

import os as _os_
import pathlib as _pathlib_

from .. import (
    _core as _core_,
    components as _components_,
    datas as _datas_,
    workflows as _workflows_,
)


# TODO mv Enviornment??
# TODO subsimulation/namespacing
# TODO AddonManager?
class Engine:
    @_functools_.cached_property
    def _workflows(self):
        return _workflows_.WorkflowManager()

    @_functools_.cached_property
    def _core(self):
        return _core_.Core()

    class InputSpecs(_typing_.NamedTuple):
        model: _datas_.Model | _os_.PathLike
        weather: _datas_.Weather | _os_.PathLike | None = None

    class OutputSpecs(_typing_.NamedTuple):
        report: _datas_.Report | _os_.PathLike | None = None

    class RuntimeOptions(_typing_.NamedTuple):
        design_day: bool = False

    # TODO status!
    def run(
        self, 
        input: InputSpecs, 
        output: OutputSpecs = OutputSpecs(),
        options: RuntimeOptions = RuntimeOptions(),
    ):
        # TODO NOTE required by energyplus
        self._core.reset()

        self._core.api.runtime \
            .set_console_output_status(
                self._core.state,
                print_output=False,
            )
        
        self._workflows.trigger(_workflows_.Workflow('run:pre', self))
        self._core.api.runtime \
            .run_energyplus(
                self._core.state,
                command_line_args=[
                    str(
                        input.model.dumpf(
                            _tempfile_.NamedTemporaryFile(suffix='.epJSON').name,
                            format='json',
                        ) 
                        if isinstance(input.model, _datas_.Model) else
                        _pathlib_.Path(input.model)
                    ),
                    *(['--weather', str(
                        input.weather.path
                        if isinstance(input.weather, _datas_.Weather) else
                        input.weather
                    )] if input.weather is not None else []),
                    '--output-directory', str((
                        output.report.path
                        if isinstance(output.report, _datas_.Report) else 
                        output.report
                        if output.report is not None else 
                        _tempfile_.TemporaryDirectory(
                            prefix='.energyplus_output_',
                        ).name
                    )),
                    *(['--design-day'] if options.design_day else []),
                ],
            )
        self._workflows.trigger(_workflows_.Workflow('run:post', self))

    # TODO stop on err!!!!!!!!!!!!!!!!!!!!!!!!!!
    def run_forever(self, *args, **kwargs):
        while True:
            self.run(*args, **kwargs)

    def stop(self):
        self._workflows.trigger(_workflows_.Workflow('stop:pre', self))
        self._core.api.runtime \
            .stop_simulation(self._core.state)
        self._workflows.trigger(_workflows_.Workflow('stop:post', self))

    # TODO
    def add(self, *components: '_components_.base.Component'):
        for component in components:
            component.__attach__(self)
        return self
    
    # TODO
    def remove(self, *components: '_components_.base.Component'):
        raise NotImplementedError
        return self

# TODO
class EngineFactory:
    pass


__all__ = [
    'Engine',
]
