"""Cross-checks against SailplaneCalcMetric.xlsx's own worked example.

The engine is unit-agnostic for every ratio/geometry formula (only wing loading, the
Reynolds proxy, and flight_performance care about which units are in play), so these
feed the metric workbook's raw mm/degree values straight into the same engine functions
used everywhere else and assert against the workbook's own displayed numbers -- an
independent source validating the mac_length/taper_ratio/sweep_angle/effective-wing
formulas adopted from that newer workbook.
"""
import pytest

from sailplane_calc.engine.geometry import compute_surface
from sailplane_calc.engine.models import PanelInput, WingInput, WingPanelInput
from sailplane_calc.engine.tail_cruciform import compute_horizontal_stab
from sailplane_calc.engine.wing import compute_wing


@pytest.fixture
def metric_wing_input() -> WingInput:
    return WingInput(
        weight_oz=0,  # not used by these assertions
        panels=[
            WingPanelInput(span=400, chord_root=205, chord_tip=200, sweep_offset=5, dihedral_rise=0),
            WingPanelInput(span=370, chord_root=200, chord_tip=150, sweep_offset=25, dihedral_rise=68.58),
            WingPanelInput(span=250, chord_root=150, chord_tip=95, sweep_offset=25, dihedral_rise=127),
            WingPanelInput(span=0, chord_root=95, chord_tip=0, sweep_offset=0, dihedral_rise=0),
        ],
    )


def test_metric_wing_geometry(metric_wing_input):
    result = compute_wing(metric_wing_input)
    surface = result.surface

    assert surface.total_span == pytest.approx(2040.00, abs=0.1)
    assert surface.aspect_ratio == pytest.approx(11.80, abs=0.02)
    assert surface.taper_ratio == pytest.approx(0.69, abs=0.01)
    assert surface.mac_length == pytest.approx(179.31, abs=0.1)
    assert surface.point_0 == pytest.approx(14.57, abs=0.1)
    assert surface.point_25 == pytest.approx(59.39, abs=0.1)
    assert surface.panel_sweep_angle_deg[0] == pytest.approx(0.7, abs=0.05)
    # "MAC distance from root" in the workbook (Wing!C44) -- the spanwise location a
    # planform diagram's AC marker sits at.
    assert surface.mac_span_location == pytest.approx(456.78, abs=0.1)


def test_mac_span_location_is_midspan_for_an_untapered_panel():
    panel = PanelInput(span=400, chord_root=150, chord_tip=150, sweep_offset=0)
    result = compute_surface([panel], mirrored=True)
    assert result.mac_span_location == pytest.approx(200.0, abs=0.001)


def test_metric_wing_effective_geometry(metric_wing_input):
    effective = compute_wing(metric_wing_input).effective
    assert effective.total_span == pytest.approx(2013.33, abs=0.5)
    assert effective.aspect_ratio == pytest.approx(11.62, abs=0.02)


def test_metric_horizontal_stabilizer():
    panel = PanelInput(span=210, chord_root=95, chord_tip=50, sweep_offset=45)
    result = compute_horizontal_stab(panel)

    assert result.total_span == pytest.approx(420.00, abs=0.1)
    assert result.mean_chord == pytest.approx(72.50, abs=0.1)
    assert result.mac_length == pytest.approx(74.83, abs=0.1)
    assert result.aspect_ratio == pytest.approx(5.79, abs=0.02)
    assert result.taper_ratio == pytest.approx(0.53, abs=0.01)
    assert result.point_0 == pytest.approx(20.17, abs=0.1)
    assert result.point_25 == pytest.approx(38.88, abs=0.1)
    assert result.panel_sweep_angle_deg[0] == pytest.approx(12.1, abs=0.05)
