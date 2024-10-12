r"""
Low-level API for interfacing with EnergyPlus.
"""


import functools as _functools_
from typing import Literal

from controllables.core.callbacks import Callback, CallbackManager


class Kernel:
    r"""
    The wrapper class for interfacing with the EnergyPlus kernel.
    This is typically used internally by the higher-level classes.
    """

    @_functools_.cached_property
    def hooks(self):
        return CallbackManager[
            Literal[
                'reset:pre', 
                'reset:post', 
                'run:pre',
                'run:post',
            ],
            Callback,
        ]()

    def __init__(self):
        r"""
        Initialize the :class:`Kernel` object.
        """

        def _hotfix10447_monkey():
            r"""
            Hotfix for issue https://github.com/NREL/EnergyPlus/issues/10446.
            Only applicable for EnergyPlus <= 23.2.*.
            """

            import energyplus.core as _energyplus_core_
            DataExchange = _energyplus_core_.pyenergyplus.datatransfer.DataExchange

            if getattr(DataExchange, '_hotfix10447', False):
                return
            
            _get_api_data = DataExchange.get_api_data
            def _hotfix10447_get_api_data(self, state):
                return [
                    DataExchange.APIDataExchangePoint(
                        _what=datapoint.what,
                        _name=datapoint.name, 
                        _key=datapoint.type, 
                        _type=datapoint.key,
                    )
                    for datapoint in (
                        _get_api_data(self, state)
                    )
                ]
            DataExchange.get_api_data = _hotfix10447_get_api_data
            setattr(DataExchange, '_hotfix10447', True)

        # TODO
        _hotfix10447_monkey()

        import energyplus.core as _energyplus_core_

        self.api = (
            _energyplus_core_.pyenergyplus
                .api.EnergyPlusAPI()
        )
        self.state = self.api.state_manager.new_state()

        self.__running__ = False

    def __repr__(self):
        return f'{type(self).__name__}()'

    def configure(self, print_output: bool | None = None):
        r"""
        Configure the simulation.

        :param print_output: Whether to print the output to `stdout`.
        """

        if print_output is not None:
            self.api.runtime.set_console_output_status(
                self.state,
                print_output=print_output,
            )

    def run(self, args: list[str]) -> int:
        r"""
        Run the simulation.

        :param args: The command-line arguments to pass to the kernel.
        :returns: The exit status code of the kernel.
        """

        # TODO pass args to hooks
        self.hooks.__call__('run:pre')
        self.__running__ = True
        res = self.api.runtime.run_energyplus(
            self.state, command_line_args=args,
        )
        self.__running__ = False
        self.hooks.__call__('run:post')
        return res
    
    @property
    def running(self) -> bool:
        r"""
        Whether the simulation is currently running.
        """

        return self.__running__
    
    def stop(self):
        r"""
        Stop the current simulation.
        """

        self.api.runtime.stop_simulation(self.state)

    def reset(self):
        r"""
        Reset the state of the :class:`Kernel` object.
        """

        self.hooks.__call__('reset:pre')
        self.api.state_manager.reset_state(self.state)
        self.hooks.__call__('reset:post')

    def __del__(self):
        r"""
        Delete the state of the :class:`Kernel` object.
        This releases the resources used by the state.
        """

        self.api.state_manager.delete_state(self.state)

    def __getstate__(self) -> object:
        r"""
        Get the state of the :class:`Kernel` object for pickling.

        .. note:: 
            No states to save as of now, 
            as `pyenergyplus` is essentially a black-box.
        """

        pass

    def __setstate__(self, _: object):
        r"""
        Set the state of the :class:`Kernel` object from a pickle.

        :param state: The state to set.

        .. seealso:: :meth:`__getstate__`.
        """

        pass


import os as _os_
import pathlib as _pathlib_

def convert_common(
    input_file: _os_.PathLike, 
    output_directory: _os_.PathLike,
    verbose: bool = False,
):
    kernel = Kernel()
    # shush
    kernel.configure(print_output=verbose)
    res = kernel.run([
        '--convert-only', 
        '--output-directory', str(output_directory),
        str(input_file),
    ])
    if res != 0:
        raise RuntimeError()

def convert_idf_to_epjson(input_file, output_directory):
    input_file, output_directory = map(_pathlib_.Path, (input_file, output_directory))
    convert_common(
        input_file=input_file, 
        output_directory=output_directory,
    )
    return output_directory / _pathlib_.Path(input_file.stem).with_suffix('.epJSON')

def convert_epjson_to_idf(input_file, output_directory):
    input_file, output_directory = map(_pathlib_.Path, (input_file, output_directory))
    convert_common(
        input_file=input_file, 
        output_directory=output_directory,
    )
    return output_directory / _pathlib_.Path(input_file.stem).with_suffix('.idf')


import pathlib as _pathlib_

InputFormats = Literal['json', 'idf']

def infer_format_from_path(path: _os_.PathLike) -> InputFormats | None:
    match _pathlib_.Path(path).suffix.lower():
        case '.json':
            return 'json'
        case '.epjson':
            return 'json'
        case '.idf':
            return 'idf'
    return None


__all__ = [
    'Kernel',
    'convert_idf_to_epjson',
    'convert_epjson_to_idf',
    'InputFormats',
    'infer_format_from_path',
]