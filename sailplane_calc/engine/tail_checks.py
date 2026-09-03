"""Tail Sizing Checks tab: Mark Drela's non-dimensional design parameters.

Works identically for a cruciform or a V-tail airframe -- the caller just builds the
`horizontal`/`vertical` TailMount from whichever geometry applies (for a V-tail, both
TailMounts wrap the same physical surface's own 25%-point but the horizontal/vertical
*equivalent* areas from `vtail_convert`, matching how the original workbook does it).
"""
from __future__ import annotations

from .geometry import safe_div
from .models import TailChecksResult, TailMount, WingInput, WingResult


def compute_eda_deg(wing_input: WingInput, wing_result: WingResult) -> float:
    """Equivalent dihedral angle: a spanwise-weighted average of the per-panel dihedral,
    weighted by an elliptical-lift-like falloff f(eta) = (1-eta^2)^1.5 at each panel break."""
    spans = [p.span for p in wing_input.panels]
    total_half_span = sum(spans)
    if total_half_span == 0:
        return 0.0

    etas = [0.0]
    cumulative = 0.0
    for span in spans:
        cumulative += span
        etas.append(cumulative / total_half_span)
    f = [(1 - eta**2) ** 1.5 for eta in etas]

    eda = 0.0
    for i, angle in enumerate(wing_result.panel_dihedral_deg):
        eda += (f[i] - f[i + 1]) * angle
    return eda


def compute_tail_checks(
    wing_input: WingInput,
    wing_result: WingResult,
    horizontal: TailMount,
    vertical: TailMount,
    cl_therm: float,
) -> TailChecksResult:
    eda_deg = compute_eda_deg(wing_input, wing_result)

    common_term = 0.75 * (wing_result.surface.mean_chord + wing_result.surface.point_0)
    horizontal_arm_term = safe_div(
        (horizontal.gap_wing_te_to_surface_le + horizontal.surface.point_25) + common_term,
        wing_result.surface.mean_chord,
    )
    vertical_arm_term = safe_div(
        (vertical.gap_wing_te_to_surface_le + vertical.surface.point_25) + common_term,
        wing_result.surface.total_span,
    )

    tail_volume_h = safe_div(horizontal.surface.total_area, wing_result.surface.total_area) * horizontal_arm_term
    tail_volume_v = safe_div(vertical.surface.total_area, wing_result.surface.total_area) * vertical_arm_term
    spiral_stability_b = eda_deg * vertical_arm_term / cl_therm if cl_therm else 0.0

    return TailChecksResult(
        eda_deg=eda_deg,
        spiral_stability_b=spiral_stability_b,
        tail_volume_h=tail_volume_h,
        tail_volume_v=tail_volume_v,
    )
