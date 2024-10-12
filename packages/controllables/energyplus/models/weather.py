r"""
TODO !!!!!!
"""


import abc as _abc_
import os as _os_


# TODO deprecate!!!!
class FileBacked(_abc_.ABC):
    def __init__(self, path: _os_.PathLike = None):
        self._path = None
        if path is not None:
            self.open(path)

    def open(self, path: _os_.PathLike) -> 'FileBacked':
        self._path = path
        return self

    @property
    def path(self) -> _os_.PathLike:
        if self._path is None:
            raise ValueError('Not `open`ed')
        return self._path


# TODO !!!!!
class WeatherModel(FileBacked):
    pass


__all__ = [
    'WeatherModel',
]