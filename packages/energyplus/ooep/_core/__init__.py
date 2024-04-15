from __future__ import annotations

import typing as _typing_

import energyplus.core as _energyplus_core_


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



import os as _os_
import pathlib as _pathlib_

def convert_common(
    input_file: _os_.PathLike, 
    output_directory: _os_.PathLike,
):
    core = Core()
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