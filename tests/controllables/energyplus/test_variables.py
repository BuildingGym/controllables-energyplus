from controllables.core import TemporaryUnavailableError
from controllables.energyplus import examples
from controllables.energyplus.systems import System
import controllables.energyplus.variables as _mod_


def variable_value_gettable(
    running_system: System, 
    variable_ref: _mod_.CommonVariable.Ref,
):
    while running_system.started:
        try: 
            running_system[variable_ref].value
            return True
        except TemporaryUnavailableError:
            pass
    return False


def variable_value_settable(
    running_system: System, 
    variable_ref: _mod_.CommonVariable.Ref,
    value,
):
    while running_system.started:
        try: 
            running_system[variable_ref].value = value
            return True
        except TemporaryUnavailableError:
            pass
    return False


class TestWallClock:
    def test_value(self):
        assert variable_value_gettable(
            examples.systems.X1ZoneUncontrolled().start(),
            _mod_.WallClock.Ref(),
        )


class TestActuator:
    def test_value(self):
        assert variable_value_gettable(
            examples.systems.X1ZoneUncontrolled().start(),
            _mod_.Actuator.Ref(
                type='Weather Data',
                control_type='Outdoor Dry Bulb',
                key='Environment',
            ),
        )

        assert variable_value_settable(
            examples.systems.X1ZoneUncontrolled().start(),
            _mod_.Actuator.Ref(
                type='Weather Data',
                control_type='Outdoor Dry Bulb',
                key='Environment',
            ),
            value=25.,
        )

    def test_reset(self):
        # TODO
        pass


class TestInternalVariable:
    def test_value(self):
        assert variable_value_gettable(
            examples.systems.X1ZoneUncontrolled().start(),
            _mod_.InternalVariable.Ref(type='Zone Floor Area', key='ZONE ONE')
        )


class TestOutputMeter:
    def test_value(self):
        assert variable_value_gettable(
            examples.systems.X1ZoneUncontrolled().start(),
            _mod_.OutputMeter.Ref(
                type='Electricity:Facility',
            ),
        )


class TestOutputVariable:
    def test_value(self):
        assert variable_value_gettable(
            examples.systems.X1ZoneUncontrolled().start(),
            _mod_.OutputVariable.Ref(
                type='Site Outdoor Air Drybulb Temperature',
                key='ENVIRONMENT',
            ),
        )
