from __future__ import annotations

import abc as _abc_
import typing as _typing_


import typing as _typing_
import functools as _functools_
import tempfile as _tempfile_

import energyplus.core as _energyplus_core_

from .. import (
    components as _components_,
    datas as _datas_,
    workflows as _workflows_,
)


# TODO subsimulation/namespacing
# TODO AddonManager?
class Engine:
    @_functools_.cached_property
    def _workflows(self):
        return _workflows_.WorkflowManager()

    @_functools_.cached_property
    def _core(self):
        class Core:
            def __init__(self):
                self.api = (
                    _energyplus_core_.pyenergyplus
                        .api.EnergyPlusAPI()
                )
                self.state = self.api.state_manager.new_state()

            def reset(self):
                self.api.state_manager.reset_state(self.state)

            def __del__(self):
                self.api.state_manager.delete_state(self.state)

        return Core()

    class InputSpecs(_typing_.NamedTuple):
        model: _datas_.Model
        weather: _datas_.Weather

    class OutputSpecs(_typing_.NamedTuple):
        report: _datas_.Report | None = None

    class RuntimeOptions(_typing_.NamedTuple):
        design_day: bool = False

    def run(
        self, 
        input: InputSpecs, 
        output: OutputSpecs = OutputSpecs(),
        options: RuntimeOptions = RuntimeOptions(),
    ):
        self._workflows.trigger(_workflows_.Workflow('run:pre', self))
        self._core.api.runtime \
            .set_console_output_status(
                self._core.state,
                print_output=False,
            )
        self._core.api.runtime \
            .run_energyplus(
                self._core.state,
                command_line_args=[
                    str(input.model.path),
                    '--weather', str(input.weather.path),
                    '--output-directory', str(
                        (output.report if output.report is not None else 
                        _datas_.Report().open(_tempfile_.TemporaryDirectory().name)).path
                    ),
                    *(['--design-day'] if options.design_day else []),
                ],
            )
        self._workflows.trigger(_workflows_.Workflow('run:post', self))

    # TODO stop on err!!!!!!!!!!!!!!!!!!!!!!!!!!
    def run_forever(self, *args, **kwargs):
        while True:
            self.reset()
            self.run(*args, **kwargs)

    def stop(self):
        self._workflows.trigger(_workflows_.Workflow('stop:pre', self))
        self._core.api.runtime \
            .stop_simulation(self._core.state)
        self._workflows.trigger(_workflows_.Workflow('stop:post', self))

    def reset(self):
        self._workflows.trigger(_workflows_.Workflow('reset:pre', self))
        self._core.reset()
        self._workflows.trigger(_workflows_.Workflow('reset:post', self))
    
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
    Engine,
]
