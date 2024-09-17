r"""
World.

Scope: "And-God-said"s, "Let-there-be"s. (Genesis 1)
"""


import functools as _functools_
import os as _os_
import threading as _threading_
from numbers import Number
from typing import (
    Literal,
    Mapping,
    Optional,
    Self,
    TypedDict,
    Unpack,
)

from controllables.core.systems import BaseSystem, SystemShortcutMixin
from controllables.core.components import BaseComponent

# TODO
from . import (
    _core as _core_,
    datas as _datas_,
)


# TODO
class World(SystemShortcutMixin, BaseSystem):
    r"""
    The world.
    Everything begins and ends here.

    TODO
    .. inheritance-diagram:: World
        :parts: -1

    Examples:

    .. code-block:: python
        # TODO

    """
    
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
        Initialize a new instance.

        :param specs: The specifications for the world. 
        :param **kwds: Entries to override in supplied :param:`specs`.
        """
        
        self._specs: World.Specs = (
            World.Specs(**(specs if specs is not None else {}), **kwds)
        )
        self._core = _core_.Core()
    
    class _CoreThread(_threading_.Thread):
        def __init__(
            self, 
            core: _core_.Core, 
            cli_args: list[str], 
            iterations: Number,
        ):
            super().__init__()
            self._core = core
            self._cli_args = cli_args
            self._iterations = iterations

        def run(self):
            while self._iterations > 0:
                self._iterations -= 1
                self._core.reset()
                self._core.configure(print_output=False)
                status = self._core.run(args=self._cli_args)
                if status != 0:
                    raise RuntimeError(
                        f'{self!r}: Operation failed with status {status}'
                    )

        def kill(self, timeout=None):
            self._core.stop()
            self.join(timeout=timeout)

    @_functools_.cached_property
    def _thread(self):
        import tempfile as _tempfile_
        import pathlib as _pathlib_

        c: World.Specs = {
            'input': self._specs['input'],
            'output': self._specs.get('output', dict()),
            'runtime': self._specs.get('runtime', dict()),
        }

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
        
        return self._CoreThread(
            core=self._core,
            cli_args=args, 
            # TODO
            iterations=float('inf') if c['runtime'].get('recurring') else 1,
        )

    def start(self):
        if self._thread.is_alive():
            raise RuntimeError(f'{self!r} is already running')
        del self._thread
        self._thread.start()
        return self
    
    @property
    def started(self):
        return self._thread.is_alive()    

    def wait(self, timeout=None):
        self._thread.join(timeout=timeout)
        return self
    
    # TODO __await__?

    def stop(self, timeout=None):
        if not self._thread.is_alive():
            raise RuntimeError(f'{self!r} is not running')
        self._thread.kill(timeout=timeout)
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


__all__ = [
    'World',
]