import typing as _typing_

from ... import base as _base_

try: 
    import gymnasium as _gymnasium_
except ImportError as e:
    raise _base_.OptionalImportError.suggest(['gymnasium']) from e

from . import utils as _utils_


# TODO more types
class SpaceStructureMapper(_utils_.StructureMapper):
    r"""
    TODO doc
    """
  
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
    r"""
    A Gymnasium space that can have a variable bound to it.
    
    This allows for the association of additional metadata or identifiers 
    with the space, which can be useful in environments where spaces 
    need to carry extra information or context.

    .. seealso::
        * `gymnasium.spaces.Space <https://gymnasium.farama.org/api/spaces/#gymnasium.spaces.Space>`_
    """
    
    def bind(self, var: T) -> _typing_.Self:
        r"""
        Bind a variable to this space.

        :param var: Variable to be associated with the current space.
        :return: This space itself.
        """
        self._binding = var
        return self
    
    # TODO err
    @property
    def binding(self) -> T:
        r"""Variable bound to this space."""
        return self._binding

class VariableBox(
    _gymnasium_.spaces.Box, 
    _typing_.Generic[T], VariableSpace[T],
):
    r"""
    A Gymnasium Box space that can have a variable bound to it.
    
    This allows for the association of additional metadata or identifiers 
    with the space, which can be useful in environments where spaces 
    need to carry extra information or context.

    Example usage:

    .. code-block:: python

        # TODO

    .. seealso::
        * `gymnasium.spaces.Box <https://gymnasium.farama.org/api/spaces/fundamental/#gymnasium.spaces.Box>`_
    """

    pass

class VariableDiscrete(
    _gymnasium_.spaces.Discrete, 
    _typing_.Generic[T], VariableSpace[T],
):
    r"""
    A Gymnasium Discrete space that can have a variable bound to it.

    Similar to :class:`VariableBox`, this allows for the association of

    .. seealso::
        * `gymnasium.spaces.Discrete <https://gymnasium.farama.org/api/spaces/fundamental/#gymnasium.spaces.Discrete>`_
    """

    pass


__all__ = [
    'VariableSpace',
    'VariableBox',
    'VariableDiscrete',
]