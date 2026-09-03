"""Data models shared by the calculation engine.

Field names and units (inches, ounces, degrees) follow SailplaneCalc.xls so results
can be checked cell-for-cell against the original workbook.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class GliderType(Enum):
    POLYHEDRAL = "polyhedral"
    AILERON_TD = "aileron_td"
    DLG = "dlg"


@dataclass
class PanelInput:
    """One trapezoidal panel of a lifting surface."""

    span: float = 0.0
    chord_root: float = 0.0
    chord_tip: float = 0.0
    # LE sweep offset (in), measured from this panel's OWN root -- not the surface root.
    sweep_offset: float = 0.0


@dataclass
class WingPanelInput(PanelInput):
    # Cumulative rise (in) at this panel's outer tip, measured from the wing-root plane
    # (i.e. what you'd read off a ruler held to the root, not the incremental rise of
    # just this panel -- the incremental angle is derived from consecutive panels' values).
    dihedral_rise: float = 0.0


@dataclass
class SurfaceResult:
    total_span: float
    total_area: float
    mean_chord: float  # simple area/span average chord
    mac_length: float  # true Mean Aerodynamic Chord length (>= mean_chord for a tapered panel)
    aspect_ratio: float
    taper_ratio: float  # tip/root for a single panel; an equivalent ratio for multi-panel surfaces
    root_chord: float
    point_0: float  # 0% MAC point, measured aft from the surface root leading edge (in)
    point_25: float  # 25% MAC point (the surface's own aerodynamic center), same reference (in)
    mac_span_location: float  # spanwise distance from the surface root where the AC marker sits (in)
    panel_areas: list[float] = field(default_factory=list)
    panel_sweep_angle_deg: list[float] = field(default_factory=list)


@dataclass
class WingInput:
    weight_oz: float
    panels: list[WingPanelInput]
    estimated_speed_mph: float = 20.0


@dataclass
class EffectiveWingResult:
    """Dihedral-projected (horizontal-plane) wing geometry -- always <= the raw totals."""

    total_span: float
    total_area: float
    mean_chord: float
    aspect_ratio: float


@dataclass
class WingResult:
    surface: SurfaceResult
    wing_loading_oz_per_ft2: float
    reynolds_estimate: float
    panel_dihedral_deg: list[float]
    root_chord: float
    effective: EffectiveWingResult


@dataclass
class VTailGeometryResult:
    surface: SurfaceResult
    half_dihedral_deg: float  # each V panel's angle up from horizontal
    total_angle_deg: float  # included angle between the two V panels


@dataclass
class TailMount:
    """How a tail surface's own geometry and where it hangs off the wing."""

    surface: SurfaceResult
    gap_wing_te_to_surface_le: float  # wing (root) trailing edge to this surface's LE (in)


@dataclass
class NeutralPointResult:
    tail_volume: float
    lift_slope_stab: float
    lift_slope_wing: float
    lift_slope_ratio: float
    downwash_factor: float
    neutral_point_pct_mac: float
    neutral_point_from_root_le: float
    neutral_point_from_root_te: float


@dataclass
class BalancePoint:
    """The three mutually-derivable views of a chosen balance point."""

    static_margin_pct: float
    cg_pct_mac: float
    cg_from_root_le: float


@dataclass
class VTailConvertResult:
    horizontal_area: float
    vertical_area: float


@dataclass
class ConventionalToVTailResult:
    v_half_area: float
    half_dihedral_deg: float
    total_angle_deg: float


@dataclass
class TailChecksResult:
    eda_deg: float
    spiral_stability_b: float
    tail_volume_h: float
    tail_volume_v: float
