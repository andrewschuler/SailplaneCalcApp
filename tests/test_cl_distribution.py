"""Structural/physical-invariant tests for the horseshoe-vortex VLM in cl_distribution.py.

We're implementing the standard VLM method rather than transcribing LIFTROLL.xlsx's own cell
formulas, so there's no spreadsheet-derived golden value to regress against here (contrast with
test_wing.py's SailplaneCalc.xls worked example) -- these checks instead verify the invariants
the method must satisfy regardless of the exact numbers: symmetry, total-lift conservation,
linearity in the target CL, and a known closed-form check on the Biot-Savart segment helper.
"""
import math

import pytest

from sailplane_calc.engine.cl_distribution import (
    ClDistributionInput,
    _segment_induced_w,
    compute_cl_distribution,
)
from sailplane_calc.engine.models import WingPanelInput


def _rect_wing(span=40.0, chord=10.0, twist=0.0) -> list[WingPanelInput]:
    return [
        WingPanelInput(span=span, chord_root=chord, chord_tip=chord, sweep_offset=0.0, twist_tip_deg=twist),
        WingPanelInput(),
        WingPanelInput(),
        WingPanelInput(),
    ]


def _tapered_wing() -> list[WingPanelInput]:
    return [
        WingPanelInput(span=18, chord_root=10.5, chord_tip=10, sweep_offset=0, dihedral_rise=0),
        WingPanelInput(span=24, chord_root=10, chord_tip=8, sweep_offset=0.8, dihedral_rise=4.25),
        WingPanelInput(span=18, chord_root=8, chord_tip=5, sweep_offset=1, dihedral_rise=10.4),
        WingPanelInput(),
    ]


def test_empty_wing_does_not_crash():
    result = compute_cl_distribution(ClDistributionInput(panels=[WingPanelInput()] * 4, target_cl=0.6))
    assert result.stations == []
    assert result.total_cl_check == 0.0


@pytest.mark.parametrize("target_cl", [0.3, 0.6, 1.0])
def test_untwisted_wing_is_symmetric(target_cl):
    result = compute_cl_distribution(ClDistributionInput(panels=_rect_wing(), target_cl=target_cl))
    n = len(result.stations)
    assert n > 0
    for i in range(n // 2):
        left = result.stations[i]
        right = result.stations[n - 1 - i]
        assert left.span_location == pytest.approx(-right.span_location, abs=1e-6)
        assert left.local_cl == pytest.approx(right.local_cl, rel=1e-6)
        assert left.local_lift == pytest.approx(right.local_lift, rel=1e-6)


@pytest.mark.parametrize("target_cl", [0.3, 0.6, 1.0])
@pytest.mark.parametrize("panels_fn", [_rect_wing, _tapered_wing])
def test_total_lift_integration_matches_target(target_cl, panels_fn):
    result = compute_cl_distribution(ClDistributionInput(panels=panels_fn(), target_cl=target_cl))
    assert result.total_cl_check == pytest.approx(target_cl, rel=1e-3)


def test_scaling_is_linear_in_target_cl():
    low = compute_cl_distribution(ClDistributionInput(panels=_tapered_wing(), target_cl=0.4))
    high = compute_cl_distribution(ClDistributionInput(panels=_tapered_wing(), target_cl=0.8))
    for s_low, s_high in zip(low.stations, high.stations):
        assert s_high.local_cl == pytest.approx(2 * s_low.local_cl, rel=1e-6)
        assert s_high.local_lift == pytest.approx(2 * s_low.local_lift, rel=1e-6)
    assert high.avg_over_max_cl_ratio == pytest.approx(low.avg_over_max_cl_ratio, rel=1e-6)


def test_untwisted_wing_root_aoa_tracks_target_cl_sign():
    positive = compute_cl_distribution(ClDistributionInput(panels=_rect_wing(), target_cl=0.6))
    assert positive.solved_root_aoa_deg > 0

    zero = compute_cl_distribution(ClDistributionInput(panels=_rect_wing(), target_cl=0.0))
    assert zero.solved_root_aoa_deg == pytest.approx(0.0, abs=1e-6)
    assert all(s.local_cl == pytest.approx(0.0, abs=1e-6) for s in zero.stations)


def test_ellipse_reference_shape_and_total():
    result = compute_cl_distribution(ClDistributionInput(panels=_tapered_wing(), target_cl=0.6))
    tip_left = result.stations[0]
    tip_right = result.stations[-1]
    root_ish = min(result.stations, key=lambda s: abs(s.span_location))

    # The outermost *station* sits at the midpoint of the outermost strip (~90% of the way to
    # the physical tip for a 5-strip-per-panel discretization), not the tip itself, so it's
    # well below the root value but not literally zero.
    assert 0 < tip_left.ellipse_lift < 0.5 * root_ish.ellipse_lift
    assert 0 < tip_right.ellipse_lift < 0.5 * root_ish.ellipse_lift
    assert root_ish.ellipse_lift == max(s.ellipse_lift for s in result.stations)
    # total_cl_check is derived from the same total_lift_analog the ellipse curve's peak (L0)
    # is scaled from, so a correct target-CL match is itself evidence the ellipse carries the
    # same total lift as the actual distribution.
    assert result.total_cl_check == pytest.approx(0.6, rel=1e-3)


def test_rectangular_wing_is_close_to_elliptical_downwash():
    """A high-AR untapered, unswept, untwisted wing's interior local Cl (excluding the
    tip-adjacent station, where a stronger gradient is physically expected) should be fairly
    uniform -- a loose plausibility bound, not an exact target."""
    result = compute_cl_distribution(ClDistributionInput(panels=_rect_wing(span=80.0, chord=5.0), target_cl=0.6))
    right_side = [s for s in result.stations if s.span_location >= 0]
    interior = right_side[:-1]  # drop the outermost (tip) station
    values = [s.local_cl for s in interior]
    mean_cl = sum(values) / len(values)
    spread = max(values) - min(values)
    assert spread < 0.25 * mean_cl


def test_segment_induced_w_matches_infinite_vortex_closed_form():
    """A long-but-finite segment along the x-axis, evaluated at a point offset by d along +y,
    should reproduce the classic infinite-straight-vortex result w = Gamma/(2*pi*d) (Gamma=1
    here) -- both sign and magnitude, before this helper gets buried inside a full horseshoe
    assembly. (Flipping which side of the line the point is on, or the segment's A->B
    direction, flips the sign -- induced velocity is antisymmetric across the filament.)"""
    half_length = 1.0e6
    d = 2.0
    w = _segment_induced_w(0.0, d, -half_length, 0.0, half_length, 0.0)
    expected = 1.0 / (2 * math.pi * d)
    assert w == pytest.approx(expected, rel=1e-3)
    assert w > 0
