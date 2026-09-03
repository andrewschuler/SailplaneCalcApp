"""Regression test using SailplaneCalc.xls's worked example (Tail Sizing Checks tab, cruciform column)."""
import pytest

from sailplane_calc.engine.models import PanelInput, TailMount, WingInput, WingPanelInput
from sailplane_calc.engine.tail_checks import compute_eda_deg, compute_tail_checks
from sailplane_calc.engine.tail_cruciform import compute_horizontal_stab, compute_vertical_fin
from sailplane_calc.engine.wing import compute_wing


@pytest.fixture
def wing_input():
    return WingInput(
        weight_oz=31,
        panels=[
            WingPanelInput(span=18, chord_root=10.5, chord_tip=10, sweep_offset=0, dihedral_rise=0),
            WingPanelInput(span=24, chord_root=10, chord_tip=8, sweep_offset=0.8, dihedral_rise=4.25),
            WingPanelInput(span=18, chord_root=8, chord_tip=5, sweep_offset=1, dihedral_rise=10.4),
        ],
        estimated_speed_mph=20,
    )


def test_eda(wing_input):
    wing_result = compute_wing(wing_input)
    eda = compute_eda_deg(wing_input, wing_result)
    assert eda == pytest.approx(12.42, abs=0.02)


def test_tail_checks_cruciform(wing_input):
    wing_result = compute_wing(wing_input)

    horizontal = TailMount(
        surface=compute_horizontal_stab(PanelInput(span=12, chord_root=5.5, chord_tip=3, sweep_offset=1.8)),
        gap_wing_te_to_surface_le=27,
    )
    vertical = TailMount(
        surface=compute_vertical_fin(
            lower=PanelInput(span=3.5, chord_root=7, chord_tip=5, sweep_offset=1),
            upper=PanelInput(span=10.5, chord_root=7, chord_tip=3, sweep_offset=1.5),
        ),
        gap_wing_te_to_surface_le=32.75,
    )

    result = compute_tail_checks(wing_input, wing_result, horizontal, vertical, cl_therm=0.6)

    assert result.eda_deg == pytest.approx(12.42, abs=0.02)
    assert result.tail_volume_h == pytest.approx(0.41, abs=0.01)
    assert result.tail_volume_v == pytest.approx(0.025, abs=0.001)
    assert result.spiral_stability_b == pytest.approx(7.17, abs=0.02)


def test_tail_checks_does_not_crash_on_empty_wing():
    """Every wing panel span cleared reduces the wing to zero area/chord/span -- must not
    raise ZeroDivisionError, since that would abort every tab's refresh()."""
    empty_wing_input = WingInput(weight_oz=31, panels=[WingPanelInput()])
    empty_wing_result = compute_wing(empty_wing_input)
    horizontal = TailMount(
        surface=compute_horizontal_stab(PanelInput(span=12, chord_root=5.5, chord_tip=3, sweep_offset=1.8)),
        gap_wing_te_to_surface_le=27,
    )
    vertical = TailMount(
        surface=compute_vertical_fin(
            lower=PanelInput(span=3.5, chord_root=7, chord_tip=5, sweep_offset=1),
            upper=PanelInput(span=10.5, chord_root=7, chord_tip=3, sweep_offset=1.5),
        ),
        gap_wing_te_to_surface_le=32.75,
    )
    result = compute_tail_checks(empty_wing_input, empty_wing_result, horizontal, vertical, cl_therm=0.6)
    assert result.tail_volume_h == 0.0
    assert result.tail_volume_v == 0.0
