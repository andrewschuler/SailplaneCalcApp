import pytest

from sailplane_calc.ui.units import (
    Units,
    from_display,
    to_display,
    unit_label,
    wing_loading_to_display,
    wing_loading_unit_label,
)


def test_imperial_is_identity():
    assert to_display(10.0, Units.IMPERIAL, "length") == 10.0
    assert from_display(10.0, Units.IMPERIAL, "weight") == 10.0


def test_length_round_trip():
    mm = to_display(1.0, Units.METRIC, "length")
    assert mm == pytest.approx(25.4, abs=0.001)
    assert from_display(mm, Units.METRIC, "length") == pytest.approx(1.0, abs=1e-9)


def test_weight_and_speed_conversion():
    assert to_display(1.0, Units.METRIC, "weight") == pytest.approx(28.3495, abs=0.001)
    assert to_display(1.0, Units.METRIC, "speed") == pytest.approx(1.609344, abs=0.0001)


def test_area_conversion():
    assert to_display(1.0, Units.METRIC, "area") == pytest.approx(0.064516, abs=1e-6)


def test_unit_labels():
    assert unit_label(Units.IMPERIAL, "length") == "in"
    assert unit_label(Units.METRIC, "length") == "mm"
    assert wing_loading_unit_label(Units.IMPERIAL) == "oz/ft²"
    assert wing_loading_unit_label(Units.METRIC) == "gr/dm²"


def test_wing_loading_imperial():
    # 31 oz over a 1035 in^2 wing, matching the app's imperial worked example.
    assert wing_loading_to_display(31, 1035, Units.IMPERIAL) == pytest.approx(4.31, abs=0.01)


def test_wing_loading_metric():
    # 400g over 35.28 dm^2 (352800 mm^2), matching the metric reference workbook's example.
    weight_oz = 400 / 28.349523125
    area_in2 = 35.28 / 0.064516
    assert wing_loading_to_display(weight_oz, area_in2, Units.METRIC) == pytest.approx(11.34, abs=0.02)
