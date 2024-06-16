import typing as _typing_

import energyplus.core as _energyplus_core_


class Core:
    r"""
    The wrapper class for interfacing with the EnergyPlus kernel (core).
    This is typically used internally by the higher-level classes.
    """

    def __init__(self):
        r"""
        Initialize the :class:`Core` object.
        """
        self.api = (
            _energyplus_core_.pyenergyplus
                .api.EnergyPlusAPI()
        )
        self.state = self.api.state_manager.new_state()

    def reset(self):
        r"""
        Reset the state of the :class:`Core` object.
        """
        self.api.state_manager.reset_state(self.state)

    def __del__(self):
        r"""
        Delete the state of the :class:`Core` object.
        This releases the resources used by the state.
        """
        self.api.state_manager.delete_state(self.state)

    def __getstate__(self) -> object:
        r"""
        Get the state of the :class:`Core` object for pickling.

        .. note:: 
            No states to save as of now, 
            as `pyenergyplus` is essentially a black-box.
        """
        pass

    def __setstate__(self, state: object):
        r"""
        Set the state of the :class:`Core` object from a pickle.

        :param state: The state to set.

        .. seealso:: :meth:`__getstate__`.
        """
        pass



import os as _os_
import pathlib as _pathlib_

def convert_common(
    input_file: _os_.PathLike, 
    output_directory: _os_.PathLike,
):
    core = Core()
    # shush
    core.api.runtime \
        .set_console_output_status(
            core.state,
            print_output=False,
        )
    res = core.api.runtime.run_energyplus(
        core.state,
        command_line_args=[
            '--convert-only', 
            '--output-directory', str(output_directory),
            str(input_file),
        ],
    )
    if res != 0:
        raise RuntimeError()

def convert_idf_to_epjson(input_file, output_directory):
    input_file, output_directory = map(_pathlib_.Path, (input_file, output_directory))
    convert_common(input_file=input_file, output_directory=output_directory)
    return output_directory / _pathlib_.Path(input_file.stem).with_suffix('.epJSON')

def convert_epjson_to_idf(input_file, output_directory):
    input_file, output_directory = map(_pathlib_.Path, (input_file, output_directory))
    convert_common(input_file=input_file, output_directory=output_directory)
    return output_directory / _pathlib_.Path(input_file.stem).with_suffix('.idf')


import pathlib as _pathlib_

Formats = _typing_.Literal['json', 'idf']

def infer_format_from_path(path: _os_.PathLike) -> Formats | None:
    match _pathlib_.Path(path).suffix.lower():
        case '.json':
            return 'json'
        case '.epjson':
            return 'json'
        case '.idf':
            return 'idf'
    return None


__all__ = [
    'Core',
    'convert_idf_to_epjson',
    'convert_epjson_to_idf',
    'Formats',
    'infer_format_from_path',
]