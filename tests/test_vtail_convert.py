"""Regression tests for the Quick V-Tail Sizing conversion, both directions."""
import pytest

from sailplane_calc.engine.vtail_convert import conventional_to_vtail, vtail_to_conventional


def test_conventional_to_vtail():
    result = conventional_to_vtail(horizontal_area=102.00, vertical_area=73.50)
    assert result.v_half_area == pytest.approx(87.75, abs=0.01)
    assert result.half_dihedral_deg == pytest.approx(35.78, abs=0.02)
    assert result.total_angle_deg == pytest.approx(108.45, abs=0.05)


def test_vtail_to_conventional():
    result = vtail_to_conventional(v_half_area=87.75, half_dihedral_deg=35.8)
    assert result.horizontal_area == pytest.approx(101.94, abs=0.05)
    assert result.vertical_area == pytest.approx(73.56, abs=0.05)


def test_round_trip():
    forward = conventional_to_vtail(horizontal_area=102.00, vertical_area=73.50)
    back = vtail_to_conventional(forward.v_half_area, forward.half_dihedral_deg)
    assert back.horizontal_area == pytest.approx(102.00, abs=0.01)
    assert back.vertical_area == pytest.approx(73.50, abs=0.01)


def test_conventional_to_vtail_zero_horizontal_area_does_not_crash():
    """Clearing the horizontal-area field to 0 would otherwise divide by zero in atan(v/h)."""
    result = conventional_to_vtail(horizontal_area=0.0, vertical_area=73.50)
    assert result.half_dihedral_deg == pytest.approx(90.0)


def test_conventional_to_vtail_both_zero_does_not_crash():
    result = conventional_to_vtail(horizontal_area=0.0, vertical_area=0.0)
    assert result.half_dihedral_deg == pytest.approx(0.0)


def test_vtail_to_conventional_minus_45_degrees_does_not_crash():
    """1 + tan(theta) hits exactly 0 at theta = -45 degrees."""
    result = vtail_to_conventional(v_half_area=50.0, half_dihedral_deg=-45.0)
    assert result.horizontal_area == 0.0
    assert result.vertical_area == 0.0
