import abc as _abc_
from typing import Generic, TypeVar

# TODO
from .spaces import Space, SpaceValT


class BasePolicy(
    _abc_.ABC,
    Generic[
        ActionSpaceT := TypeVar('ActionSpaceT', Space, covariant=True),
        ObservationSpaceT := TypeVar('ObservationSpaceT', Space, covariant=True),
    ],
):
    action_space: ActionSpaceT
    observation_space: ObservationSpaceT

    @_abc_.abstractmethod
    def compute_action(self, observation: SpaceValT) -> SpaceValT:
        ...

