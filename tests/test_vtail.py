"""Regression test using the V-Tail reference workbook's own worked example (V-Tail tab)."""
import pytest

from sailplane_calc.engine.models import PanelInput
from sailplane_calc.engine.tail_vtail import compute_vtail, compute_vtail_equivalent_areas


def test_vtail_geometry():
    panel = PanelInput(span=20.65, chord_root=5.5, chord_tip=3, sweep_offset=0.86)
    result = compute_vtail(panel, dihedral_rise=14.9)

    assert result.surface.total_span == pytest.approx(41.30, abs=0.01)
    assert result.surface.total_area == pytest.approx(175.53, abs=0.01)
    assert result.surface.mean_chord == pytest.approx(4.25, abs=0.01)
    assert result.surface.aspect_ratio == pytest.approx(9.72, abs=0.01)
    assert result.surface.panel_areas == pytest.approx([87.76], abs=0.01)
    # point_0/point_25 use compute_surface's own general aggregation, unmodified -- the
    # original workbook's own point_25 quirk (see git history) does not persist in the newer
    # reference workbook's V-Tail sheet, which reproduces the general formula exactly.
    assert result.surface.point_25 == pytest.approx(1.481, abs=0.001)
    # half_dihedral = asin(rise/span) -- the panel span is a physical/slant length, matching
    # the reference workbook's own ASIN-based formula (not atan).
    assert result.half_dihedral_deg == pytest.approx(46.18, abs=0.05)
    assert result.total_angle_deg == pytest.approx(87.63, abs=0.1)


def test_vtail_equivalent_areas():
    """The horizontal/vertical stabilizer areas a V-tail panel is equivalent to for CG/tail-
    checks purposes: a cos^2/sin^2 split of its own total area by dihedral angle -- distinct
    from vtail_convert.vtail_to_conventional's tangent-based Quick V-Tail Sizing conversion."""
    panel = PanelInput(span=20.65, chord_root=5.5, chord_tip=3, sweep_offset=0.86)
    vtail = compute_vtail(panel, dihedral_rise=14.9)
    equivalent = compute_vtail_equivalent_areas(vtail)

    assert equivalent.horizontal_area == pytest.approx(84.14, abs=0.05)
    assert equivalent.vertical_area == pytest.approx(91.38, abs=0.05)
    # cos^2 + sin^2 = 1, so the two equivalent areas always sum back to the V-tail's own total.
    assert equivalent.horizontal_area + equivalent.vertical_area == pytest.approx(
        vtail.surface.total_area, abs=0.01
    )


def test_vtail_equivalent_areas_zero_span_does_not_crash():
    panel = PanelInput(span=0, chord_root=5.5, chord_tip=3, sweep_offset=0.86)
    vtail = compute_vtail(panel, dihedral_rise=14.9)
    equivalent = compute_vtail_equivalent_areas(vtail)
    assert equivalent.horizontal_area == 0.0
    assert equivalent.vertical_area == 0.0
