"""Regression test using SailplaneCalc.xls's worked example (Cruciform Tail tab)."""
import pytest

from sailplane_calc.engine.models import PanelInput
from sailplane_calc.engine.tail_cruciform import compute_horizontal_stab, compute_vertical_fin


def test_horizontal_stab():
    panel = PanelInput(span=12, chord_root=5.5, chord_tip=3, sweep_offset=1.8)
    result = compute_horizontal_stab(panel)

    assert result.total_span == pytest.approx(24.00, abs=0.01)
    assert result.total_area == pytest.approx(102.00, abs=0.01)
    assert result.mean_chord == pytest.approx(4.25, abs=0.01)
    assert result.aspect_ratio == pytest.approx(5.65, abs=0.01)
    # point_0/point_25 use the true MAC length, not the area/span mean chord -- see
    # geometry.compute_surface.
    assert result.point_0 == pytest.approx(0.812, abs=0.001)
    assert result.point_25 == pytest.approx(1.905, abs=0.001)
    assert result.mac_length == pytest.approx(4.373, abs=0.001)
    assert result.taper_ratio == pytest.approx(0.545, abs=0.001)
    assert result.panel_sweep_angle_deg == pytest.approx([8.53], abs=0.01)


def test_vertical_fin():
    lower = PanelInput(span=3.5, chord_root=7, chord_tip=5, sweep_offset=1)
    upper = PanelInput(span=10.5, chord_root=7, chord_tip=3, sweep_offset=1.5)
    result = compute_vertical_fin(lower, upper)

    assert result.total_span == pytest.approx(14.00, abs=0.01)
    assert result.total_area == pytest.approx(73.50, abs=0.01)
    assert result.mean_chord == pytest.approx(5.25, abs=0.01)
    assert result.point_0 == pytest.approx(0.599, abs=0.001)
    assert result.point_25 == pytest.approx(1.972, abs=0.001)
    assert result.mac_length == pytest.approx(5.492, abs=0.001)
    assert result.taper_ratio == pytest.approx(0.5, abs=0.001)
    assert result.panel_areas == pytest.approx([21.00, 52.50], abs=0.01)
