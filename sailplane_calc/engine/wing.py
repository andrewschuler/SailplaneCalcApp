"""Wing tab: up to 4 tapered/swept/polyhedral panels."""
from __future__ import annotations

import math

from .geometry import compute_surface
from .models import EffectiveWingResult, WingInput, WingPanelInput, WingResult


def incremental_rise(panels: list[WingPanelInput]) -> list[float]:
    """Each panel's own rise, relative to the previous panel's cumulative rise -- the
    `dihedral_rise` field stores a cumulative measurement (see WingPanelInput's docstring)."""
    diffs: list[float] = []
    prev_rise = 0.0
    for p in panels:
        diffs.append(p.dihedral_rise - prev_rise)
        prev_rise = p.dihedral_rise
    return diffs


def compute_panel_dihedral_deg(panels: list[WingPanelInput]) -> list[float]:
    """Per-panel dihedral angle from each panel's cumulative-rise measurement.

    A rise larger in magnitude than the panel's own span is physically extreme (it implies
    more than 90 degrees of dihedral) but not unreachable while a user is mid-edit -- e.g.
    shrinking a span below a rise that was already entered for it. Clamping the asin
    argument to [-1, 1] saturates the angle at +/-90 degrees instead of raising, since a
    domain error here would abort every tab's refresh() (they all call compute_wing).
    """
    angles: list[float] = []
    for p, rise_diff in zip(panels, incremental_rise(panels)):
        if p.span > 0:
            ratio = max(-1.0, min(1.0, rise_diff / p.span))
            angles.append(math.degrees(math.asin(ratio)))
        else:
            angles.append(0.0)
    return angles


def compute_effective_wing(panels: list[WingPanelInput], weight_oz: float) -> EffectiveWingResult:
    """Dihedral-projected (horizontal-plane) span/area/AR/loading: a panel's surface span is a
    slant length once it has dihedral, so its aerodynamically-relevant (projected) span is
    shorter, and the wing loading computed against that smaller area is correspondingly higher
    than the raw "Total Wing Results" wing loading."""
    effective_spans: list[float] = []
    panel_areas: list[float] = []
    for p, rise_diff in zip(panels, incremental_rise(panels)):
        if p.span <= 0:
            continue
        inside = p.span**2 - rise_diff**2
        eff_span = math.sqrt(inside) if inside > 0 else 0.0
        effective_spans.append(eff_span)
        panel_areas.append(eff_span * (p.chord_root + p.chord_tip) / 2)

    raw_eff_span = sum(effective_spans)
    if raw_eff_span == 0:
        return EffectiveWingResult(0.0, 0.0, 0.0, 0.0, 0.0)

    raw_eff_area = sum(panel_areas)
    total_span = raw_eff_span * 2
    mean_chord = raw_eff_area / raw_eff_span
    total_area = total_span * mean_chord
    aspect_ratio = total_span / mean_chord
    wing_loading = weight_oz / total_area * 144 if total_area else 0.0
    return EffectiveWingResult(
        total_span=total_span,
        total_area=total_area,
        mean_chord=mean_chord,
        aspect_ratio=aspect_ratio,
        wing_loading_oz_per_ft2=wing_loading,
    )


def compute_dihedral_rise_from_angles(spans: list[float], angles_deg: list[float]) -> list[float]:
    """Dihedral Converter: inverse of compute_panel_dihedral_deg -- given each panel's span and
    dihedral angle, returns the cumulative rise at each panel's tip (what to measure with a
    ruler), for entering into the main span/rise inputs."""
    rises: list[float] = []
    cumulative = 0.0
    for span, angle in zip(spans, angles_deg):
        cumulative += math.sin(math.radians(angle)) * span
        rises.append(cumulative)
    return rises


def compute_wing(wing_input: WingInput) -> WingResult:
    surface = compute_surface(list(wing_input.panels), mirrored=True)
    wing_loading = (
        wing_input.weight_oz / surface.total_area * 144 if surface.total_area else 0.0
    )
    reynolds_estimate = 9360 * wing_input.estimated_speed_mph * (surface.mean_chord * 0.0833333)
    panel_dihedral_deg = compute_panel_dihedral_deg(wing_input.panels)
    root_chord = wing_input.panels[0].chord_root if wing_input.panels else 0.0
    effective = compute_effective_wing(wing_input.panels, wing_input.weight_oz)
    return WingResult(
        surface=surface,
        wing_loading_oz_per_ft2=wing_loading,
        reynolds_estimate=reynolds_estimate,
        panel_dihedral_deg=panel_dihedral_deg,
        root_chord=root_chord,
        effective=effective,
    )
