"""Outline geometry used to draw each surface's planform diagram (ui/planform_widget.py)."""
import pytest

from sailplane_calc.engine.models import PanelInput
from sailplane_calc.engine.planform import (
    compute_fin_outline,
    compute_fin_panels,
    compute_planform_outline,
    compute_planform_panels,
)


def test_single_untapered_panel_is_a_clean_rectangle():
    panel = PanelInput(span=20, chord_root=5, chord_tip=5, sweep_offset=0)
    outline = compute_planform_outline([panel], mirror=False)
    assert outline == pytest.approx([(0.0, 0.0), (20.0, 0.0), (20.0, 5.0), (0.0, 5.0)])


def test_single_panel_mirrored_doubles_the_span():
    panel = PanelInput(span=20, chord_root=5, chord_tip=5, sweep_offset=0)
    outline = compute_planform_outline([panel], mirror=True)
    spans = [s for s, _ in outline]
    assert min(spans) == pytest.approx(-20.0)
    assert max(spans) == pytest.approx(20.0)
    # Symmetric about span=0: every (s, c) has a (-s, c) counterpart.
    for s, c in outline:
        assert any(s2 == pytest.approx(-s, abs=1e-9) and c2 == pytest.approx(c) for s2, c2 in outline)


def test_tapered_swept_wing_outline():
    panels = [
        PanelInput(span=18, chord_root=10.5, chord_tip=10, sweep_offset=0),
        PanelInput(span=24, chord_root=10, chord_tip=8, sweep_offset=0.8),
        PanelInput(span=18, chord_root=8, chord_tip=5, sweep_offset=1),
    ]
    outline = compute_planform_outline(panels, mirror=False)

    # 4 leading-edge points (root + 3 tips) + 4 trailing-edge points, closed polygon.
    assert len(outline) == 8

    le_points = outline[:4]
    te_points = list(reversed(outline[4:]))
    assert le_points == pytest.approx(
        [(0.0, 0.0), (18.0, 0.0), (42.0, 0.8), (60.0, 1.8)]
    )
    # Trailing edge = leading edge x-offset + chord at every breakpoint.
    assert te_points == pytest.approx(
        [(0.0, 10.5), (18.0, 10.0), (42.0, 8.8), (60.0, 6.8)]
    )


def test_panels_with_zero_span_are_excluded():
    panels = [
        PanelInput(span=18, chord_root=10.5, chord_tip=10, sweep_offset=0),
        PanelInput(span=0, chord_root=10, chord_tip=0, sweep_offset=0),
    ]
    outline = compute_planform_outline(panels, mirror=False)
    assert len(outline) == 4  # only the one active panel


def test_empty_panels_returns_empty_outline():
    assert compute_planform_outline([], mirror=False) == []


def test_fin_outline_extends_in_opposite_directions():
    lower = PanelInput(span=3.5, chord_root=7, chord_tip=5, sweep_offset=1)
    upper = PanelInput(span=10.5, chord_root=7, chord_tip=3, sweep_offset=1.5)
    outline = compute_fin_outline(lower, upper)

    assert outline == pytest.approx(
        [(-3.5, 1.0), (0.0, 0.0), (10.5, 1.5), (10.5, 4.5), (0.0, 7.0), (-3.5, 6.0)]
    )
    spans = [s for s, _ in outline]
    assert min(spans) < 0 < max(spans)


def test_fin_outline_with_only_upper_panel():
    lower = PanelInput(span=0, chord_root=7, chord_tip=0, sweep_offset=0)
    upper = PanelInput(span=10.5, chord_root=7, chord_tip=3, sweep_offset=1.5)
    outline = compute_fin_outline(lower, upper)
    assert all(s >= 0 for s, _ in outline)
    assert len(outline) == 4


def test_planform_panels_unmirrored_indices_and_quads():
    panels = [
        PanelInput(span=18, chord_root=10.5, chord_tip=10, sweep_offset=0),
        PanelInput(span=24, chord_root=10, chord_tip=8, sweep_offset=0.8),
    ]
    result = compute_planform_panels(panels, mirror=False)
    assert [idx for idx, _ in result] == [0, 1]

    idx0, quad0 = result[0]
    assert quad0 == pytest.approx([(0.0, 0.0), (18.0, 0.0), (18.0, 10.0), (0.0, 10.5)])

    idx1, quad1 = result[1]
    assert quad1 == pytest.approx([(18.0, 0.0), (42.0, 0.8), (42.0, 8.8), (18.0, 10.0)])


def test_planform_panels_mirrored_shares_index_per_side():
    panels = [PanelInput(span=18, chord_root=10.5, chord_tip=10, sweep_offset=0)]
    result = compute_planform_panels(panels, mirror=True)
    assert len(result) == 2
    assert result[0][0] == result[1][0] == 0
    spans_side_a = [s for s, _ in result[0][1]]
    spans_side_b = [s for s, _ in result[1][1]]
    assert (min(spans_side_a) >= 0) != (min(spans_side_b) >= 0)  # opposite sides


def test_planform_panels_skips_inactive_panels():
    panels = [
        PanelInput(span=18, chord_root=10.5, chord_tip=10, sweep_offset=0),
        PanelInput(span=0, chord_root=10, chord_tip=0, sweep_offset=0),
    ]
    result = compute_planform_panels(panels, mirror=False)
    assert len(result) == 1
    assert result[0][0] == 0


def test_fin_panels_stable_indices():
    lower = PanelInput(span=3.5, chord_root=7, chord_tip=5, sweep_offset=1)
    upper = PanelInput(span=10.5, chord_root=7, chord_tip=3, sweep_offset=1.5)
    result = compute_fin_panels(lower, upper)
    assert dict(result).keys() == {0, 1}
    lower_quad = dict(result)[0]
    upper_quad = dict(result)[1]
    assert all(s <= 0 for s, _ in lower_quad)
    assert all(s >= 0 for s, _ in upper_quad)


def test_fin_panels_only_upper_keeps_index_one():
    lower = PanelInput(span=0, chord_root=7, chord_tip=0, sweep_offset=0)
    upper = PanelInput(span=10.5, chord_root=7, chord_tip=3, sweep_offset=1.5)
    result = compute_fin_panels(lower, upper)
    assert result == [(1, dict(result)[1])]
