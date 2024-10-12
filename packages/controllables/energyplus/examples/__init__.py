r"""
Simple examples (default).

TODO doc
"""


from typing import Unpack

try:
    from energyplus.dataset.basic import dataset as _epds_
except ModuleNotFoundError:
    from controllables.core.errors import OptionalModuleNotFoundError
    raise OptionalModuleNotFoundError.suggest(['energyplus-dataset'])

from ..systems import System


class files:
    class buildings:
        X1ZoneUncontrolled = _epds_.models / '1ZoneUncontrolled.idf'
        X1ZoneEvapCooler = _epds_.models / '1ZoneEvapCooler.idf'
        X5ZoneAirCooled = _epds_.models / '5ZoneAirCooled.idf'

    class weathers:
        DenverAuroraBuckleyAFB = _epds_.weathers / 'USA_CO_Denver-Aurora-Buckley.AFB.724695_TMY3.epw'


class configs:
    X1ZoneUncontrolled = System.Config(
        building=files.buildings.X1ZoneUncontrolled,
        weather=files.weathers.DenverAuroraBuckleyAFB,
    )

    X1ZoneEvapCooler = System.Config(
        building=files.buildings.X1ZoneEvapCooler,
        weather=files.weathers.DenverAuroraBuckleyAFB,
    )

    X5ZoneAirCooled = System.Config(
        building=files.buildings.X5ZoneAirCooled,
        weather=files.weathers.DenverAuroraBuckleyAFB,
    )


class systems:
    @classmethod
    def X1ZoneUncontrolled(cls, **config_kwds: Unpack[System.Config]):
        return System(config=configs.X1ZoneUncontrolled, **config_kwds)

    @classmethod
    def X1ZoneEvapCooler(cls, **config_kwds: Unpack[System.Config]):
        return System(config=configs.X1ZoneEvapCooler, **config_kwds)

    @classmethod
    def X5ZoneAirCooled(cls, **config_kwds: Unpack[System.Config]):
        return System(config=configs.X5ZoneAirCooled, **config_kwds)


__all__ = [
    'files',
    'configs',
    'systems',
]