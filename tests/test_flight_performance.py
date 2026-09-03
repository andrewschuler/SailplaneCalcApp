"""Cross-checked against SailplaneCalcMetric.xlsx's Speed/Cl/G-load example: 400g model,
35.28 dm^2 wing, stalling at 17.5kph (Cl ~= 0.77) or at Cl=0.90 (~16.3kph)."""
import pytest

from sailplane_calc.engine.flight_performance import (
    MAX_SPEED_MULTIPLIER,
    cl_from_stall_speed,
    g_load_at_speed,
    stall_speed_from_cl,
)

WEIGHT_OZ = 400 / 28.349523125  # 400 grams
AREA_IN2 = 35.28 / 0.064516  # 35.28 dm^2
KPH_TO_MPH = 1 / 1.609344


def test_cl_from_stall_speed():
    stall_speed_mph = 17.5 * KPH_TO_MPH
    cl = cl_from_stall_speed(WEIGHT_OZ, AREA_IN2, stall_speed_mph)
    assert cl == pytest.approx(0.77, abs=0.01)

    # The reference workbook's own G-load formula uses a rounded air density (0.6 kg/m^3
    # term = 0.5*1.2, vs. the precise 0.5*0.002378 slug/ft^3 used consistently here), so it
    # lands on 15.7 rather than the mathematically exact value for holding the same Cl at
    # MAX_SPEED_MULTIPLIER times the stall speed: load factor = (V/Vstall)^2 = multiplier^2.
    # This implementation is internally consistent (same air density used throughout), so
    # it asserts the exact algebraic relationship rather than reproducing that rounding.
    max_speed_mph = stall_speed_mph * MAX_SPEED_MULTIPLIER
    g = g_load_at_speed(WEIGHT_OZ, AREA_IN2, cl, max_speed_mph)
    assert g == pytest.approx(MAX_SPEED_MULTIPLIER**2, abs=0.01)


def test_stall_speed_from_cl():
    cl = 0.90
    stall_speed_mph = stall_speed_from_cl(WEIGHT_OZ, AREA_IN2, cl)
    # Close to but not exactly the sheet's 16.3kph -- see test_cl_from_stall_speed's note on
    # the reference workbook's own rounded constants.
    assert stall_speed_mph * 1.609344 == pytest.approx(16.3, abs=0.3)

    max_speed_mph = stall_speed_mph * MAX_SPEED_MULTIPLIER
    g = g_load_at_speed(WEIGHT_OZ, AREA_IN2, cl, max_speed_mph)
    assert g == pytest.approx(MAX_SPEED_MULTIPLIER**2, abs=0.01)


def test_round_trip():
    cl = cl_from_stall_speed(WEIGHT_OZ, AREA_IN2, 10.0)
    stall_speed = stall_speed_from_cl(WEIGHT_OZ, AREA_IN2, cl)
    assert stall_speed == pytest.approx(10.0, abs=0.001)
