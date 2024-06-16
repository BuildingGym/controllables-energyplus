import abc as _abc_
import os as _os_


class FileBacked(_abc_.ABC):
    def __init__(self):
        self._path = None

    def open(self, path: _os_.PathLike) -> 'FileBacked':
        self._path = path
        return self

    @property
    def path(self) -> _os_.PathLike:
        if self._path is None:
            raise ValueError('Not `open`ed')
        return self._path



import typing as _typing_
import collections as _collections_

import json as _json_
import os as _os_
import tempfile as _tempfile_


from .. import _core as _core_


# TODO mv WorldModel
class InputModel(_collections_.UserDict):
    r"""
    The input model.
    This represents an epJSON object.

    .. seealso:: https://energyplus.readthedocs.io/en/latest/schema.html
    """

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
    ) -> _typing_.Self:
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


class WeatherModel(FileBacked):
    pass

# TODO
class Report(FileBacked):
    pass


__all__ = [
    'InputModel',
    'WeatherModel',
    'Report',
]
