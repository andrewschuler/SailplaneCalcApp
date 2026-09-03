"""Cruciform Tail CG / V-Tail CG tabs: neutral point and balance-point (CG) analysis.

Method: tail-volume-coefficient neutral point estimate (Simons), with a Helmbold-style
aspect-ratio correction to each surface's lift-curve slope and an empirical downwash factor.
"""
from __future__ import annotations

import math

from .geometry import safe_div as _div
from .models import BalancePoint, NeutralPointResult, SurfaceResult, VTailGeometryResult, WingResult


def _helmbold_lift_slope(aspect_ratio: float, a0: float) -> float:
    return (aspect_ratio * a0) / (aspect_ratio + 18.25 * a0) if (aspect_ratio + 18.25 * a0) else 0.0


def _finish(
    wing: WingResult,
    tail_volume: float,
    lift_slope_stab: float,
    lift_slope_wing: float,
    stab_efficiency: float,
) -> NeutralPointResult:
    ratio = _div(lift_slope_stab, lift_slope_wing)
    downwash = 35 * _div(lift_slope_wing, wing.surface.aspect_ratio)
    np_pct = (0.25 + stab_efficiency * tail_volume * ratio * (1 - downwash)) * 100
    np_from_le = wing.surface.point_0 + wing.surface.mean_chord * np_pct / 100
    np_from_te = wing.root_chord - np_from_le
    return NeutralPointResult(
        tail_volume=tail_volume,
        lift_slope_stab=lift_slope_stab,
        lift_slope_wing=lift_slope_wing,
        lift_slope_ratio=ratio,
        downwash_factor=downwash,
        neutral_point_pct_mac=np_pct,
        neutral_point_from_root_le=np_from_le,
        neutral_point_from_root_te=np_from_te,
    )


def compute_neutral_point_cruciform(
    wing: WingResult,
    horizontal_stab: SurfaceResult,
    gap_wing_te_to_stab_le: float,
    stab_efficiency: float,
) -> NeutralPointResult:
    tail_arm = (
        horizontal_stab.point_25
        + (wing.root_chord - wing.surface.point_25)
        + gap_wing_te_to_stab_le
    )
    tail_volume = _div(
        horizontal_stab.total_area * tail_arm, wing.surface.total_area * wing.surface.mean_chord
    )
    lift_slope_stab = _helmbold_lift_slope(horizontal_stab.aspect_ratio, 0.095)
    lift_slope_wing = _helmbold_lift_slope(wing.surface.aspect_ratio, 0.11)
    return _finish(wing, tail_volume, lift_slope_stab, lift_slope_wing, stab_efficiency)


def compute_neutral_point_vtail(
    wing: WingResult,
    vtail: VTailGeometryResult,
    horizontal_equivalent_area: float,
    gap_wing_te_to_vtail_le: float,
    stab_efficiency: float,
) -> NeutralPointResult:
    cos_factor = math.cos(math.radians(vtail.half_dihedral_deg))
    tail_arm = (
        vtail.surface.point_25 + (wing.root_chord - wing.surface.point_25) + gap_wing_te_to_vtail_le
    )
    tail_volume = _div(
        horizontal_equivalent_area * cos_factor * tail_arm,
        wing.surface.total_area * wing.surface.mean_chord,
    )
    lift_slope_stab = _helmbold_lift_slope(vtail.surface.aspect_ratio, 0.095) * cos_factor
    lift_slope_wing = _helmbold_lift_slope(wing.surface.aspect_ratio, 0.11)
    return _finish(wing, tail_volume, lift_slope_stab, lift_slope_wing, stab_efficiency)


def compute_balance_point(
    wing: WingResult,
    neutral_point: NeutralPointResult,
    *,
    static_margin_pct: float | None = None,
    cg_pct_mac: float | None = None,
    cg_from_root_le: float | None = None,
) -> BalancePoint:
    """Exactly one of the three keyword args selects how the balance point is specified;
    the other two are derived from it."""
    given = [v for v in (static_margin_pct, cg_pct_mac, cg_from_root_le) if v is not None]
    if len(given) != 1:
        raise ValueError("Provide exactly one of static_margin_pct, cg_pct_mac, cg_from_root_le")

    if static_margin_pct is not None:
        cg_pct = neutral_point.neutral_point_pct_mac - static_margin_pct
    elif cg_pct_mac is not None:
        cg_pct = cg_pct_mac
    else:
        assert cg_from_root_le is not None
        cg_pct = _div(cg_from_root_le - wing.surface.point_0, wing.surface.mean_chord) * 100

    static_margin = neutral_point.neutral_point_pct_mac - cg_pct
    cg_le = wing.surface.point_0 + wing.surface.mean_chord * cg_pct / 100
    return BalancePoint(static_margin_pct=static_margin, cg_pct_mac=cg_pct, cg_from_root_le=cg_le)
