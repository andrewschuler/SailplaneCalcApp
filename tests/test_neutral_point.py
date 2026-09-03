"""Regression tests for Cruciform Tail CG / V-Tail CG using the workbook's worked example."""
import pytest

from sailplane_calc.engine.models import PanelInput, WingInput, WingPanelInput
from sailplane_calc.engine.neutral_point import (
    compute_balance_point,
    compute_neutral_point_cruciform,
    compute_neutral_point_vtail,
)
from sailplane_calc.engine.tail_cruciform import compute_horizontal_stab
from sailplane_calc.engine.tail_vtail import compute_vtail
from sailplane_calc.engine.vtail_convert import vtail_to_conventional
from sailplane_calc.engine.wing import compute_wing


@pytest.fixture
def wing_result():
    wing_input = WingInput(
        weight_oz=31,
        panels=[
            WingPanelInput(span=18, chord_root=10.5, chord_tip=10, sweep_offset=0, dihedral_rise=0),
            WingPanelInput(span=24, chord_root=10, chord_tip=8, sweep_offset=0.8, dihedral_rise=4.25),
            WingPanelInput(span=18, chord_root=8, chord_tip=5, sweep_offset=1, dihedral_rise=10.4),
        ],
        estimated_speed_mph=20,
    )
    return compute_wing(wing_input)


def test_neutral_point_cruciform(wing_result):
    stab = compute_horizontal_stab(PanelInput(span=12, chord_root=5.5, chord_tip=3, sweep_offset=1.8))
    np_result = compute_neutral_point_cruciform(
        wing_result, stab, gap_wing_te_to_stab_le=27, stab_efficiency=0.60
    )

    assert np_result.tail_volume == pytest.approx(0.42, abs=0.01)
    assert np_result.lift_slope_stab == pytest.approx(0.073, abs=0.002)
    assert np_result.lift_slope_wing == pytest.approx(0.096, abs=0.002)
    assert np_result.lift_slope_ratio == pytest.approx(0.76, abs=0.01)
    assert np_result.downwash_factor == pytest.approx(0.242, abs=0.005)
    assert np_result.neutral_point_pct_mac == pytest.approx(39.43, abs=0.1)
    # from_root_le/te use wing point_0/mean_chord with the mac_length-based point_0 -- see
    # geometry.compute_surface.
    assert np_result.neutral_point_from_root_le == pytest.approx(3.847, abs=0.01)
    assert np_result.neutral_point_from_root_te == pytest.approx(6.653, abs=0.01)


def test_balance_point_scenarios_cruciform(wing_result):
    stab = compute_horizontal_stab(PanelInput(span=12, chord_root=5.5, chord_tip=3, sweep_offset=1.8))
    np_result = compute_neutral_point_cruciform(
        wing_result, stab, gap_wing_te_to_stab_le=27, stab_efficiency=0.60
    )

    by_margin = compute_balance_point(wing_result, np_result, static_margin_pct=6.3)
    assert by_margin.cg_pct_mac == pytest.approx(33.13, abs=0.05)
    assert by_margin.cg_from_root_le == pytest.approx(3.304, abs=0.01)

    by_distance = compute_balance_point(wing_result, np_result, cg_from_root_le=3.61)
    assert by_distance.cg_pct_mac == pytest.approx(36.68, abs=0.05)
    assert by_distance.static_margin_pct == pytest.approx(2.75, abs=0.05)

    by_pct = compute_balance_point(wing_result, np_result, cg_pct_mac=36)
    assert by_pct.cg_from_root_le == pytest.approx(3.551, abs=0.01)
    assert by_pct.static_margin_pct == pytest.approx(3.43, abs=0.05)


def test_neutral_point_vtail(wing_result):
    vtail = compute_vtail(
        PanelInput(span=20.65, chord_root=5.5, chord_tip=3, sweep_offset=0.86), dihedral_rise=14.9
    )
    equivalent = vtail_to_conventional(
        v_half_area=vtail.surface.panel_areas[0], half_dihedral_deg=vtail.half_dihedral_deg
    )
    np_result = compute_neutral_point_vtail(
        wing_result,
        vtail,
        horizontal_equivalent_area=equivalent.horizontal_area,
        gap_wing_te_to_vtail_le=27,
        stab_efficiency=0.60,
    )

    assert equivalent.horizontal_area == pytest.approx(101.96, abs=0.05)
    assert equivalent.vertical_area == pytest.approx(73.57, abs=0.05)
    assert np_result.tail_volume == pytest.approx(0.34, abs=0.01)
    assert np_result.lift_slope_stab == pytest.approx(0.065, abs=0.002)
    assert np_result.lift_slope_ratio == pytest.approx(0.68, abs=0.01)
    assert np_result.downwash_factor == pytest.approx(0.24, abs=0.005)
    assert np_result.neutral_point_pct_mac == pytest.approx(35.52, abs=0.1)
    assert np_result.neutral_point_from_root_le == pytest.approx(3.509, abs=0.01)
    assert np_result.neutral_point_from_root_te == pytest.approx(6.991, abs=0.01)


def test_neutral_point_cruciform_does_not_crash_on_empty_wing():
    """Every wing panel span cleared (e.g. mid-edit) reduces the wing to zero area/chord --
    must not raise ZeroDivisionError, since that would abort every tab's refresh()."""
    empty_wing = compute_wing(WingInput(weight_oz=31, panels=[WingPanelInput()]))
    stab = compute_horizontal_stab(PanelInput(span=12, chord_root=5.5, chord_tip=3, sweep_offset=1.8))

    np_result = compute_neutral_point_cruciform(
        empty_wing, stab, gap_wing_te_to_stab_le=27, stab_efficiency=0.60
    )
    assert np_result.tail_volume == 0.0

    balance = compute_balance_point(empty_wing, np_result, cg_from_root_le=3.0)
    assert balance.cg_pct_mac == 0.0
