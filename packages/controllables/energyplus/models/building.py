r"""
TODO
"""


import collections as _collections_
import json as _json_
import os as _os_
import tempfile as _tempfile_
from typing import Self

from .. import _core as _core_


class BuildingModel(_collections_.UserDict):
    r"""
    The building model.
    This represents an epJSON object.

    .. seealso:: https://energyplus.readthedocs.io/en/latest/schema.html
    """

    @classmethod
    def from_buffer(cls, buffer: bytes):
        return cls().load(buffer)

    @classmethod
    def from_file(cls, path: _os_.PathLike):
        return cls().loadf(path)

    Formats = _core_.Formats

    def load(self, fp):
        self.data = _json_.load(fp)
        return self

    def dump(self, fp):
        _json_.dump(self.data, fp)
        return fp
    
    def loadf(
        self, 
        path: _os_.PathLike, 
        format: Formats = None,
    ) -> Self:
        format = (
            format if format is not None else 
            _core_.infer_format_from_path(path)
        )
        match format:
            case 'json':
                path = path
            case 'idf':
                tempdir_ref = _tempfile_.TemporaryDirectory()
                path = _core_.convert_idf_to_epjson(
                    input_file=path,
                    output_directory=tempdir_ref.name,
                )
            case _:
                raise ValueError()

        with open(path, mode='r') as fp:
            self.load(fp)

        return self
    
    def dumpf(
        self, 
        path: _os_.PathLike,
        format: Formats = None,
    ) -> _os_.PathLike:
        format = (
            format if format is not None else 
            _core_.infer_format_from_path(path)
        )
        match format:
            case 'json':
                path = path
            # TODO
            case 'idf':
                raise NotImplementedError('TODO')
            case _:
                raise ValueError()
            
        with open(path, mode='w') as fp:
            self.dump(fp)

        return path
    

__all__ = [
    'BuildingModel',
]