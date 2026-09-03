"""Regression test using SailplaneCalc.xls's own worked example (Wing tab)."""
import pytest

from sailplane_calc.engine.models import WingInput, WingPanelInput
from sailplane_calc.engine.wing import compute_dihedral_rise_from_angles, compute_wing


@pytest.fixture
def example_wing_input() -> WingInput:
    return WingInput(
        weight_oz=31,
        panels=[
            WingPanelInput(span=18, chord_root=10.5, chord_tip=10, sweep_offset=0, dihedral_rise=0),
            WingPanelInput(span=24, chord_root=10, chord_tip=8, sweep_offset=0.8, dihedral_rise=4.25),
            WingPanelInput(span=18, chord_root=8, chord_tip=5, sweep_offset=1, dihedral_rise=10.4),
        ],
        estimated_speed_mph=20,
    )


def test_wing_totals(example_wing_input):
    result = compute_wing(example_wing_input)
    surface = result.surface

    assert surface.total_span == pytest.approx(120.00, abs=0.01)
    assert surface.total_area == pytest.approx(1035.00, abs=0.01)
    assert surface.mean_chord == pytest.approx(8.63, abs=0.01)
    assert surface.aspect_ratio == pytest.approx(13.91, abs=0.01)
    # point_0/point_25 use the true MAC length (not the simple area/span mean chord) for the
    # *0.25 term -- see geometry.compute_surface -- so these differ slightly from a naive
    # area/span-based calculation.
    assert surface.point_0 == pytest.approx(0.446, abs=0.001)
    assert surface.point_25 == pytest.approx(2.677, abs=0.001)
    assert surface.mac_length == pytest.approx(8.923, abs=0.001)
    assert surface.taper_ratio == pytest.approx(0.643, abs=0.001)
    assert result.wing_loading_oz_per_ft2 == pytest.approx(4.31, abs=0.01)
    assert result.reynolds_estimate == pytest.approx(134550, abs=1)
    assert result.root_chord == 10.5


def test_wing_panel_sweep_angle(example_wing_input):
    result = compute_wing(example_wing_input)
    assert result.surface.panel_sweep_angle_deg == pytest.approx([0.0, 1.909, 3.180], abs=0.01)


def test_wing_effective_geometry(example_wing_input):
    """Dihedral-projected span/area/AR should be <= the raw totals whenever there's dihedral."""
    result = compute_wing(example_wing_input)
    effective = result.effective
    surface = result.surface

    assert effective.total_span < surface.total_span
    assert effective.total_area < surface.total_area
    assert effective.aspect_ratio < surface.aspect_ratio
    assert effective.total_span == pytest.approx(117.075, abs=0.01)
    assert effective.total_area == pytest.approx(1014.09, abs=0.1)
    assert effective.aspect_ratio == pytest.approx(13.516, abs=0.01)
    assert effective.wing_loading_oz_per_ft2 == pytest.approx(4.40, abs=0.01)


def test_wing_four_panels():
    """A 4th panel behaves like the others -- included in totals when it has span."""
    wing_input = WingInput(
        weight_oz=31,
        panels=[
            WingPanelInput(span=18, chord_root=10.5, chord_tip=10, sweep_offset=0, dihedral_rise=0),
            WingPanelInput(span=24, chord_root=10, chord_tip=8, sweep_offset=0.8, dihedral_rise=4.25),
            WingPanelInput(span=18, chord_root=8, chord_tip=5, sweep_offset=1, dihedral_rise=10.4),
            WingPanelInput(span=10, chord_root=5, chord_tip=3, sweep_offset=1.2, dihedral_rise=13.5),
        ],
    )
    result = compute_wing(wing_input)
    assert len(result.surface.panel_areas) == 4
    assert result.surface.total_span == pytest.approx(140.00, abs=0.01)


def test_dihedral_converter_round_trip(example_wing_input):
    """Angle -> rise should invert the engine's own rise -> angle calc."""
    result = compute_wing(example_wing_input)
    spans = [p.span for p in example_wing_input.panels]
    rises = compute_dihedral_rise_from_angles(spans, result.panel_dihedral_deg)
    assert rises == pytest.approx([p.dihedral_rise for p in example_wing_input.panels], abs=0.01)


def test_wing_panel_areas(example_wing_input):
    result = compute_wing(example_wing_input)
    assert result.surface.panel_areas == pytest.approx([184.50, 216.00, 117.00], abs=0.01)


def test_wing_panel_dihedral(example_wing_input):
    result = compute_wing(example_wing_input)
    assert result.panel_dihedral_deg == pytest.approx([0.0, 10.2, 20.0], abs=0.1)


def test_dihedral_exceeding_span_does_not_crash():
    """A rise larger than its panel's own span (e.g. from shrinking the span after the rise
    was already set) implies an asin argument outside [-1, 1] -- must saturate at +/-90
    degrees rather than raising, since that would abort every tab's refresh()."""
    wing_input = WingInput(
        weight_oz=31,
        panels=[
            WingPanelInput(span=18, chord_root=10.5, chord_tip=10, sweep_offset=0, dihedral_rise=0),
            # rise (28.12) far exceeds this panel's own span (4.0) -- reproduces the reported
            # "ValueError: expected a number in range from -1 up to 1, got 1.5621" crash.
            WingPanelInput(span=4, chord_root=10, chord_tip=8, sweep_offset=0.8, dihedral_rise=28.12),
        ],
    )
    result = compute_wing(wing_input)
    assert result.panel_dihedral_deg[1] == pytest.approx(90.0)


def test_negative_dihedral_exceeding_span_saturates_at_minus_90():
    wing_input = WingInput(
        weight_oz=31,
        panels=[
            WingPanelInput(span=18, chord_root=10.5, chord_tip=10, sweep_offset=0, dihedral_rise=-40),
        ],
    )
    result = compute_wing(wing_input)
    assert result.panel_dihedral_deg[0] == pytest.approx(-90.0)


def test_wing_with_only_two_panels():
    """Third panel disabled (span=0) should be excluded from totals, matching the sheet's
    'enter zeros for the third panel' guidance."""
    wing_input = WingInput(
        weight_oz=31,
        panels=[
            WingPanelInput(span=18, chord_root=10.5, chord_tip=10, sweep_offset=0, dihedral_rise=0),
            WingPanelInput(span=24, chord_root=10, chord_tip=8, sweep_offset=0.8, dihedral_rise=4.25),
            WingPanelInput(span=0, chord_root=0, chord_tip=0, sweep_offset=0, dihedral_rise=4.25),
        ],
    )
    result = compute_wing(wing_input)
    assert result.surface.total_span == pytest.approx(84.00, abs=0.01)
    assert len(result.surface.panel_areas) == 2
