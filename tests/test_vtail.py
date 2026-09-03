"""Regression test using SailplaneCalc.xls's worked example (V-Tail tab), including the
workbook's own point_25 quirk (see tail_vtail.py docstring)."""
import pytest

from sailplane_calc.engine.models import PanelInput
from sailplane_calc.engine.tail_vtail import compute_vtail


def test_vtail_geometry():
    panel = PanelInput(span=20.65, chord_root=5.5, chord_tip=3, sweep_offset=0.86)
    result = compute_vtail(panel, dihedral_rise=14.9)

    assert result.surface.total_span == pytest.approx(41.30, abs=0.01)
    assert result.surface.total_area == pytest.approx(175.53, abs=0.01)
    assert result.surface.mean_chord == pytest.approx(4.25, abs=0.01)
    assert result.surface.aspect_ratio == pytest.approx(9.72, abs=0.01)
    assert result.surface.panel_areas == pytest.approx([87.76], abs=0.01)
    # Uses mac_length (not mean_chord) for the *0.25 term -- see tail_vtail.py docstring.
    assert result.surface.point_25 == pytest.approx(1.869, abs=0.001)
    assert result.half_dihedral_deg == pytest.approx(35.8, abs=0.05)
    assert result.total_angle_deg == pytest.approx(108.4, abs=0.1)
