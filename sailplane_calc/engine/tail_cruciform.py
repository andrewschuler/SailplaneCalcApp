"""Cruciform Tail tab: a single-panel horizontal stabilizer plus a two-panel vertical fin.

The vertical fin's lower and upper panels both root at the shared center chord and extend
independently below/above it (not a chained stack like the Wing's panels), so their MAC
locations are computed independently before being combined -- see `compute_vertical_fin`.
"""
from __future__ import annotations

from .geometry import (
    compute_surface,
    panel_25pct_from_own_root,
    panel_mac_length,
    panel_mac_span_location,
    panel_sweep_angle_deg,
)
from .models import PanelInput, SurfaceResult


def compute_horizontal_stab(panel: PanelInput) -> SurfaceResult:
    return compute_surface([panel], mirrored=True)


def compute_vertical_fin(lower: PanelInput, upper: PanelInput) -> SurfaceResult:
    # (panel, sign) -- the lower panel extends below the shared root/center-chord, so its
    # spanwise MAC contribution is negated: a coherent "below/above the fuselage centerline"
    # convention for a vertical fin, rather than a placeholder value.
    signed_panels = [(p, sign) for p, sign in ((lower, -1.0), (upper, 1.0)) if p.span > 0]
    raw_span = sum(p.span for p, _ in signed_panels)
    if raw_span == 0:
        return SurfaceResult(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, [], [])

    panel_areas: list[float] = []
    sweep_angles: list[float] = []
    weighted_x_sum = 0.0
    weighted_mac_sum = 0.0
    weighted_mac_span_sum = 0.0
    for p, sign in signed_panels:
        area = p.span * (p.chord_root + p.chord_tip) / 2
        x = panel_25pct_from_own_root(p.chord_root, p.chord_tip, p.sweep_offset)
        mac_span = panel_mac_span_location(p.chord_root, p.chord_tip, p.span)
        panel_areas.append(area)
        sweep_angles.append(panel_sweep_angle_deg(p.sweep_offset, p.span))
        weighted_x_sum += area * x
        weighted_mac_sum += area * panel_mac_length(p.chord_root, p.chord_tip)
        weighted_mac_span_sum += area * sign * mac_span

    raw_area = sum(panel_areas)
    mean_chord = raw_area / raw_span
    mac_length = weighted_mac_sum / raw_area
    mac_span_location = weighted_mac_span_sum / raw_area
    total_span = raw_span  # not mirrored: lower/upper panels are already the full fin
    total_area = total_span * mean_chord
    aspect_ratio = total_span / mean_chord
    root_chord = signed_panels[0][0].chord_root  # the shared center chord
    taper_ratio = 2 * mean_chord / root_chord - 1 if root_chord else 0.0
    point_0 = weighted_x_sum / total_area - mac_length * 0.25
    point_25 = point_0 + mac_length * 0.25

    return SurfaceResult(
        total_span=total_span,
        total_area=total_area,
        mean_chord=mean_chord,
        mac_length=mac_length,
        aspect_ratio=aspect_ratio,
        taper_ratio=taper_ratio,
        root_chord=root_chord,
        point_0=point_0,
        point_25=point_25,
        mac_span_location=mac_span_location,
        panel_areas=panel_areas,
        panel_sweep_angle_deg=sweep_angles,
    )


def compute_vertical_fin_panel_taper_ratios(lower: PanelInput, upper: PanelInput) -> tuple[float, float]:
    """Per-panel taper ratio for the fin's two independently-rooted panels -- distinct from
    SurfaceResult.taper_ratio's whole-fin aggregate (which blends both panels' MAC against the
    shared root and has no counterpart here, since a fin whose panels share a root but aren't
    chained tip-to-tip like the wing has no single well-defined "one taper ratio" the way a
    chained wing panel does). Returns (lower_taper_ratio, upper_taper_ratio)."""
    center_chord = upper.chord_root or lower.chord_root  # shared root/center chord

    def _taper(p: PanelInput) -> float:
        if p.span <= 0 or center_chord == 0:
            return 0.0
        mean_chord = (p.chord_root + p.chord_tip) / 2
        return 2 * mean_chord / center_chord - 1

    return _taper(lower), _taper(upper)
