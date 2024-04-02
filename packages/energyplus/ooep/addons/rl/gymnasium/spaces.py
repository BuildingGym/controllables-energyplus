import typing as _typing_

from ... import base as _base_

try: 
    import gymnasium as _gymnasium_
except ImportError as e:
    raise _base_.OptionalImportError(['gymnasium']) from e

from .... import utils as _utils_


# TODO more types
class SpaceStructureMapper(_utils_.mappings.StructureMapper):
    _struct_types = {
        dict: (dict, _gymnasium_.spaces.Dict, ),
        **{
            t: (t, _gymnasium_.spaces.Tuple, )
            for t in (tuple, list, set)
        },
    }

T = _typing_.TypeVar('T')

class VariableSpace(
    _gymnasium_.spaces.Space, 
    _typing_.Generic[T],
):
    def bind(self, var: T) -> _typing_.Self:
        self._binding = var
        return self
    
    # TODO err
    @property
    def binding(self) -> T:
        return self._binding

class VariableBox(
    _gymnasium_.spaces.Box, 
    _typing_.Generic[T], VariableSpace[T],
):
    pass

__all__ = [
    VariableSpace,
    VariableBox,
]