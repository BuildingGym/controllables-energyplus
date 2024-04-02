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

class Weather(FileBacked):
    pass

class Model(FileBacked):
    pass

class Report(FileBacked):
    pass

__all__ = [
    Weather,
    Model,
    Report,
]
