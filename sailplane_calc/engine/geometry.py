"""Shared trapezoidal-panel surface math (Wing, Cruciform Tail, V-Tail all reduce to this).

`mirrored=True` means the panel spans are half-span measurements of a symmetric surface
(wing, horizontal stab, V-tail half) that gets doubled for the full surface; `mirrored=False`
means the panels already describe the full surface (the cruciform vertical fin's lower/upper
panels, which are not left-right mirrored).
"""
from __future__ import annotations

import math

from .models import PanelInput, SurfaceResult


def safe_div(numerator: float, denominator: float) -> float:
    """A wing/tail surface reduced to zero (e.g. every panel span cleared while mid-edit)
    would otherwise raise ZeroDivisionError wherever its area/chord/span is a divisor,
    aborting every tab's refresh() that depends on it -- 0.0 is a reasonable placeholder
    result until the geometry is filled back in."""
    return numerator / denominator if denominator else 0.0


def panel_25pct_from_own_root(chord_root: float, chord_tip: float, sweep_offset: float) -> float:
    """25%-MAC location of a single trapezoidal panel, from that panel's own root LE."""
    c_sum = chord_root + chord_tip
    if c_sum == 0:
        return 0.0
    return (
        sweep_offset * (chord_root + 2 * chord_tip) / 3 / c_sum
        + (c_sum - chord_root * chord_tip / c_sum) / 6
    )


def panel_mac_length(chord_root: float, chord_tip: float) -> float:
    """True Mean Aerodynamic Chord length of a single trapezoidal panel (>= its area/span
    average chord for any tapered panel) -- distinct from the surface's overall `mean_chord`."""
    c_sum = chord_root + chord_tip
    if c_sum == 0:
        return 0.0
    return (2 / 3) * (chord_root + (chord_tip - (chord_root * chord_tip) / c_sum))


def panel_sweep_angle_deg(sweep_offset: float, span: float) -> float:
    """Leading-edge sweep angle of a single panel, purely informational."""
    if span <= 0:
        return 0.0
    return math.degrees(math.atan(sweep_offset / span))


def panel_mac_span_location(chord_root: float, chord_tip: float, span: float) -> float:
    """Spanwise position (0..span, from this panel's own root) where the local chord equals
    this panel's own MAC length -- where a planform diagram's AC marker sits chordwise."""
    if chord_root == chord_tip:
        return span / 2
    mac = panel_mac_length(chord_root, chord_tip)
    return span * (chord_root - mac) / (chord_root - chord_tip)


def compute_surface(panels: list[PanelInput], mirrored: bool) -> SurfaceResult:
    active = [p for p in panels if p.span > 0]
    raw_span = sum(p.span for p in active)
    if raw_span == 0:
        return SurfaceResult(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, [], [])

    cumulative_sweep = 0.0
    cumulative_span = 0.0
    panel_areas: list[float] = []
    sweep_angles: list[float] = []
    weighted_x_sum = 0.0
    weighted_mac_sum = 0.0
    weighted_mac_span_sum = 0.0
    for p in active:
        area = p.span * (p.chord_root + p.chord_tip) / 2
        x_from_surface_root = (
            panel_25pct_from_own_root(p.chord_root, p.chord_tip, p.sweep_offset) + cumulative_sweep
        )
        mac_span_from_surface_root = (
            panel_mac_span_location(p.chord_root, p.chord_tip, p.span) + cumulative_span
        )
        panel_areas.append(area)
        sweep_angles.append(panel_sweep_angle_deg(p.sweep_offset, p.span))
        weighted_x_sum += area * x_from_surface_root
        weighted_mac_sum += area * panel_mac_length(p.chord_root, p.chord_tip)
        weighted_mac_span_sum += area * mac_span_from_surface_root
        cumulative_sweep += p.sweep_offset
        cumulative_span += p.span

    raw_area = sum(panel_areas)
    factor = 2.0 if mirrored else 1.0
    total_span = raw_span * factor
    mean_chord = raw_area / raw_span
    mac_length = weighted_mac_sum / raw_area
    mac_span_location = weighted_mac_span_sum / raw_area
    total_area = total_span * mean_chord
    aspect_ratio = total_span / mean_chord
    root_chord = active[0].chord_root
    taper_ratio = 2 * mean_chord / root_chord - 1 if root_chord else 0.0
    point_0 = weighted_x_sum / total_area * factor - mac_length * 0.25
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
