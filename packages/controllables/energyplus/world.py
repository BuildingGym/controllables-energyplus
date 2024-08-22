r"""
World.

Scope: "And-God-said"s, "Let-there-be"s. (Genesis 1)
"""


import enum as _enum_
import functools as _functools_
import os as _os_
from typing import (
    Literal,
    Mapping,
    Optional,
    Self,
    TypedDict,
    Unpack,
)

from controllables.core import BaseSystem, SystemShortcutMixin
from controllables.core.specs.components import BaseComponent

from . import (
    _core as _core_,
    datas as _datas_,
)


# TODO subsimulation/namespacing
# TODO AddonManager?
class World(SystemShortcutMixin, BaseSystem):
    r"""
    The world.
    Everything begins and ends here.

    Examples:

    .. code-block:: python
        # TODO

    """

    class State(_enum_.Enum):
        r"""
        The state of the world.
        """

        IDLE = 0
        r"""The world is idle."""

        RUNNING = 1
        r"""The world is running."""

        STOPPING = 2
        r"""The world is stopping."""
    
    class Specs(TypedDict):
        r"""
        Specifications for the world.
        """

        class Input(TypedDict):
            r"""
            The input specifications.
            """

            world: _datas_.WorldModel | _os_.PathLike
            r"""The world model or the path to the world model."""

            weather: Optional[_datas_.WeatherModel | _os_.PathLike | None]
            r"""The weather model or the path to the weather model."""

        class Output(TypedDict):
            r"""
            The output specifications.
            """

            report: Optional[_datas_.Report | _os_.PathLike | None]
            r"""The report or the path to the report to generate."""

        class Runtime(TypedDict):
            r"""
            The runtime specifications.
            This controls the runtime behavior of the world.
            """

            recurring: Optional[bool | None]
            r"""
            Whether to run repeatedly.
            TODO max n epoches/runs.
            """

            design_day: Optional[bool | None]
            r"""
            Whether to run in design day mode.

            ..seealso:: https://energyplus.readthedocs.io/en/latest/tips_and_tricks/tips_and_tricks.html#design-day-creation
            """

        input: Input
        r"""The input specifications."""

        output: Optional[Output | None]
        r"""The output specifications."""
        
        runtime: Optional[Runtime | None]
        r"""The runtime specifications."""

    def __init__(
        self, 
        specs: Specs | Mapping | None = None, 
        **kwds: Unpack[Specs],
    ):
        r"""
        Initialize a new instance of :class:`Engine`.

        :param specs: The specifications for the world. 
        :param **kwds: Entries to override in supplied :param:`specs`.
        """
        
        self._specs: World.Specs = (
            World.Specs(**(specs if specs is not None else {}), **kwds)
        )
        self._state: World.State = World.State.IDLE
    
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

        self.__init__(specs)

    @_functools_.cached_property
    def _core(self):
        r"""
        The kernel.
        """

        return _core_.Core()

    def run(self):        
        import tempfile as _tempfile_
        import pathlib as _pathlib_

        if self._state != World.State.IDLE:
            raise RuntimeError(f'Engine is currently running: {self._state}.')

        c: World.Specs = {
            'input': self._specs['input'],
            'output': self._specs.get('output', dict()),
            'runtime': self._specs.get('runtime', dict()),
        }

        keepalive = True

        while keepalive:
            # NOTE state must be reset between runs
            self._core.reset()

            self._core.api.runtime \
                .set_console_output_status(
                    self._core.state,
                    print_output=False,
                )
            
            args = [
                # 0
                str(
                    c['input']['world'].dumpf(
                        _tempfile_.NamedTemporaryFile(suffix='.epJSON').name,
                        format='json',
                    ) 
                    if isinstance(c['input']['world'], _datas_.WorldModel) else
                    _pathlib_.Path(c['input']['world'])
                ),
                # "--output-directory"
                '--output-directory', 
                str(
                    c['output']['report'].path
                    if isinstance(c['output']['report'], _datas_.Report) else 
                    c['output']['report']
                ) 
                if c['output'].get('report') is not None else 
                _tempfile_.TemporaryDirectory(
                    prefix='.energyplus_output_',
                ).name,
            ]
            if c['input'].get('weather') is not None:
                args.extend([
                    '--weather', str(
                        c['input']['weather'].path
                        if isinstance(c['input']['weather'], _datas_.WeatherModel) else
                        c['input']['weather']
                    ),
                ])
            if c['runtime'].get('design_day') is True:
                args.extend(['--design-day'])
            
            self.workflows.__call__('run:pre')

            self._state = World.State.RUNNING
            status = self._core.api.runtime \
                .run_energyplus(
                    self._core.state,
                    command_line_args=args,
                )
            if (self._state == World.State.STOPPING 
                    or not c['runtime'].get('recurring')):
                keepalive = False
            self._state = World.State.IDLE
            if status != 0:
                raise RuntimeError(f'Operation failed with status {status}.')
            
            self.workflows.__call__('run:post')

        return self

    def stop(self):
        if self._state == World.State.IDLE:
            raise RuntimeError(f'World is not running: {self._state}.')

        self.workflows.__call__('stop:pre')
        self._state = World.State.STOPPING
        self._core.api.runtime \
            .stop_simulation(self._core.state)
        self.workflows.__call__('stop:post')

        return self
    
    @_functools_.cached_property
    def events(self):
        from .events import EventManager
        return EventManager().__attach__(self)

    @_functools_.cached_property
    def variables(self):
        from .variables import VariableManager
        return VariableManager().__attach__(self)
    
    def add(
        self, 
        component: BaseComponent[Self] 
            | Literal['logging:message', 'logging:progress']
    ):
        match component:
            case 'logging:message':
                from .logging.message import MessageLogger
                component = MessageLogger()
            case 'logging:progress':
                from .logging.progress import ProgressLogger
                component = ProgressLogger()
            case _:
                pass
        return super().add(component)


__all__ = [
    'World',
]
