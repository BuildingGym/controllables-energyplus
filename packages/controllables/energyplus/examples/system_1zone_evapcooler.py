r"""
TODO
"""


from types import SimpleNamespace
from os import PathLike
# TODO
from energyplus.dataset.basic import dataset as _epds_

from ..systems import System


class Paths:
    building_model: PathLike
    weather_model: PathLike


paths: Paths = SimpleNamespace(
    building_model=_epds_.models / '1ZoneEvapCooler.idf',
    weather_model=_epds_.weathers / 'USA_CO_Denver-Aurora-Buckley.AFB.724695_TMY3.epw',
)


def make_system(**config_kwds):
    return System(
        building=paths.building_model,
        weather=paths.weather_model,
        **config_kwds,
    )


__all__ = [
    'paths',
    'make_system',
]