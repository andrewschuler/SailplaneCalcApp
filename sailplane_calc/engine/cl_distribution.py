"""Local Cl / lift-distribution calculator: a horseshoe-vortex Vortex Lattice Method (VLM),
ported from the classic RC-soaring "LIFTROLL" spreadsheet method (LIFTROLL.xlsx), applied to
the same 4-panel wing geometry the Wing tab already collects.

Everything is solved on a single flat (chordwise, spanwise) plane -- LIFTROLL's own vortex
corners are stored as 2-D pairs, so dihedral plays no part in the induced-velocity geometry
here either; each panel's dihedral-projected (effective) span is used instead, the same
projection `wing.compute_effective_wing` already applies, via the shared `wing.incremental_rise`
helper.

Circulation is linear in angle of attack, so rather than an aileron/roll-rate goal-seek (the way
LIFTROLL's own Excel Solver finds roll trim), this module solves the linear system once for two
independent right-hand sides -- the wing's built-in twist, and a unit root angle of attack -- and
combines them in closed form to hit a target overall CL (the aircraft's CL at stall speed, from
AppState.speed_performance(), already gathered on the Wing tab).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .geometry import compute_surface, safe_div
from .linalg import solve_linear_system
from .models import WingPanelInput
from .wing import incremental_rise

# Spanwise strips per panel, per side. 4 panels x 5 stations x 2 (mirrored) sides = up to 40
# horseshoe vortices, matching LIFTROLL's own fixed 40-vortex grid. More stations gives a
# smoother chart at the cost of an (N^3) solve; 5 is a good balance for a live-refreshing UI.
N_STATIONS_PER_PANEL = 5

# Trailing legs are extended this many span-lengths downstream rather than solved as true
# semi-infinite vortex filaments -- a standard, well-known long-but-finite stand-in (the
# residual induced velocity beyond this distance is negligible) that lets one finite-segment
# Biot-Savart formula serve both the bound and trailing legs.
TRAILING_LEG_LENGTH_FACTOR = 100

_EPS = 1e-9


@dataclass
class SpanStationResult:
    span_location: float  # inches from centerline; negative = left; list is sorted ascending
    chord: float
    local_cl: float
    local_lift: float  # Cl * chord == 2*circulation/V-infinity (inches)
    ellipse_lift: float  # ideal elliptical reference, same total lift & (effective) span


@dataclass
class ClDistributionInput:
    panels: list[WingPanelInput]
    target_cl: float  # overall wing CL to scale the solved distribution to


@dataclass
class ClDistributionResult:
    stations: list[SpanStationResult] = field(default_factory=list)
    root_local_cl: float = 0.0
    tip_local_cl: float = 0.0
    max_local_cl: float = 0.0
    max_local_cl_location: float = 0.0
    avg_over_max_cl_ratio: float = 0.0  # target_cl / max_local_cl -- LIFTROLL's "av/mx Cl"
    solved_root_aoa_deg: float = 0.0
    total_cl_check: float = 0.0  # integrated CL of the solved distribution -- should == target_cl


def _build_span_stations(panels: list[WingPanelInput]) -> tuple[list[dict], float]:
    """Right-side (positive-span) vortex/control-point geometry, one dict per spanwise strip,
    plus the total effective (dihedral-projected) half-span. Follows the same active-panel,
    cumulative-span/sweep walk as `planform.compute_planform_panels`, chaining twist the same
    way chord and sweep already chain (a panel's own root twist = the previous panel's tip
    twist; the first active panel's root twist is 0)."""
    rises = incremental_rise(panels)
    cumulative_span = 0.0
    cumulative_sweep = 0.0
    cumulative_twist = 0.0
    stations: list[dict] = []
    for p, rise_diff in zip(panels, rises):
        if p.span <= 0:
            continue
        inside = p.span**2 - rise_diff**2
        eff_span = math.sqrt(inside) if inside > 0 else 0.0
        if eff_span <= 0:
            continue

        root_twist = cumulative_twist
        tip_twist = p.twist_tip_deg
        for i in range(N_STATIONS_PER_PANEL):
            t0 = i / N_STATIONS_PER_PANEL
            t1 = (i + 1) / N_STATIONS_PER_PANEL
            tmid = (t0 + t1) / 2
            y0 = cumulative_span + eff_span * t0
            y1 = cumulative_span + eff_span * t1
            chord0 = p.chord_root + (p.chord_tip - p.chord_root) * t0
            chord1 = p.chord_root + (p.chord_tip - p.chord_root) * t1
            chord_mid = p.chord_root + (p.chord_tip - p.chord_root) * tmid
            le0 = cumulative_sweep + p.sweep_offset * t0
            le1 = cumulative_sweep + p.sweep_offset * t1
            le_mid = cumulative_sweep + p.sweep_offset * tmid
            stations.append(
                {
                    "bound_left": (le0 + 0.25 * chord0, y0),
                    "bound_right": (le1 + 0.25 * chord1, y1),
                    "control_point": (le_mid + 0.75 * chord_mid, cumulative_span + eff_span * tmid),
                    "chord": chord_mid,
                    "twist_deg": root_twist + (tip_twist - root_twist) * tmid,
                    "span_location": cumulative_span + eff_span * tmid,
                    "width": y1 - y0,
                }
            )

        cumulative_span += eff_span
        cumulative_sweep += p.sweep_offset
        cumulative_twist = tip_twist

    return stations, cumulative_span


def _mirror_stations(stations: list[dict]) -> list[dict]:
    """Mirrors right-side stations to the left, negating span position and swapping which
    bound-vortex corner is "left"/"right" so the whole wing keeps one consistent left-to-right
    circulation traversal direction (same convention `planform.compute_planform_outline` uses
    when it reverses its mirrored point list)."""
    mirrored = []
    for s in stations:
        lx, ly = s["bound_left"]
        rx, ry = s["bound_right"]
        cx, cy = s["control_point"]
        mirrored.append(
            {
                "bound_left": (rx, -ry),
                "bound_right": (lx, -ly),
                "control_point": (cx, -cy),
                "chord": s["chord"],
                "twist_deg": s["twist_deg"],
                "span_location": -s["span_location"],
                "width": s["width"],
            }
        )
    return mirrored


def _segment_induced_w(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    """Downwash (the only nonzero induced-velocity component, since every point lies in the
    same flat plane) at (px, py) from a unit-circulation straight vortex filament A->B, per the
    standard finite-vortex-segment Biot-Savart formula (Katz & Plotkin, *Low-Speed
    Aerodynamics*, Sec. 10.4)."""
    r1x, r1y = px - ax, py - ay
    r2x, r2y = px - bx, py - by
    r0x, r0y = bx - ax, by - ay
    cross_z = r1x * r2y - r1y * r2x
    n1 = math.hypot(r1x, r1y)
    n2 = math.hypot(r2x, r2y)
    if abs(cross_z) < _EPS or n1 < _EPS or n2 < _EPS:
        return 0.0
    k = (r0x * r1x + r0y * r1y) / n1 - (r0x * r2x + r0y * r2y) / n2
    return (1.0 / (4 * math.pi)) * (k / cross_z)


def _horseshoe_induced_w(px: float, py: float, left: tuple, right: tuple, far_x: float) -> float:
    """One horseshoe vortex's downwash at (px, py): a far-downstream-to-left trailing leg, the
    left-to-right bound segment, and a right-to-far-downstream trailing leg -- one continuous
    circulation loop."""
    lx, ly = left
    rx, ry = right
    w = _segment_induced_w(px, py, far_x, ly, lx, ly)
    w += _segment_induced_w(px, py, lx, ly, rx, ry)
    w += _segment_induced_w(px, py, rx, ry, far_x, ry)
    return w


def compute_cl_distribution(cl_input: ClDistributionInput) -> ClDistributionResult:
    panels = cl_input.panels
    if not any(p.span > 0 for p in panels):
        return ClDistributionResult()

    surface = compute_surface(panels, mirrored=True)
    if surface.total_area <= 0:
        return ClDistributionResult()

    right_stations, half_span = _build_span_stations(panels)
    if not right_stations or half_span <= 0:
        return ClDistributionResult()

    stations = list(reversed(_mirror_stations(right_stations))) + right_stations
    far_x = TRAILING_LEG_LENGTH_FACTOR * (2 * half_span)

    n = len(stations)
    aic = [[0.0] * n for _ in range(n)]
    rhs_twist: list[float] = []
    rhs_unit: list[float] = []
    for i, si in enumerate(stations):
        px, py = si["control_point"]
        for k, sk in enumerate(stations):
            aic[i][k] = _horseshoe_induced_w(px, py, sk["bound_left"], sk["bound_right"], far_x)
        # Flow-tangency boundary condition (w_induced = -V-infinity * alpha_local, V-infinity
        # normalized to 1): verified against a known-sign single-panel case -- positive local
        # AOA must resolve to positive circulation (positive lift), not negative.
        rhs_twist.append(-math.radians(si["twist_deg"]))
        rhs_unit.append(-1.0)

    solved = solve_linear_system(aic, [[t, u] for t, u in zip(rhs_twist, rhs_unit)])
    gamma_twist = [row[0] for row in solved]
    gamma_unit = [row[1] for row in solved]

    def integrated_cl(gamma: list[float]) -> float:
        total_lift_analog = sum(2 * g * s["width"] for g, s in zip(gamma, stations))
        return total_lift_analog / surface.total_area

    cl_twist = integrated_cl(gamma_twist)
    cl_unit = integrated_cl(gamma_unit)
    alpha_root = safe_div(cl_input.target_cl - cl_twist, cl_unit)

    gamma = [gt + alpha_root * gu for gt, gu in zip(gamma_twist, gamma_unit)]
    total_lift_analog = sum(2 * g * s["width"] for g, s in zip(gamma, stations))
    total_cl_check = total_lift_analog / surface.total_area

    ellipse_l0 = safe_div(2 * total_lift_analog, math.pi * half_span)

    stations_out: list[SpanStationResult] = []
    for s, g in zip(stations, gamma):
        local_lift = 2 * g
        local_cl = safe_div(local_lift, s["chord"])
        ellipse_lift = ellipse_l0 * math.sqrt(max(0.0, 1 - (s["span_location"] / half_span) ** 2))
        stations_out.append(
            SpanStationResult(
                span_location=s["span_location"],
                chord=s["chord"],
                local_cl=local_cl,
                local_lift=local_lift,
                ellipse_lift=ellipse_lift,
            )
        )

    right_side = [s for s in stations_out if s.span_location >= 0]
    root_local_cl = right_side[0].local_cl if right_side else 0.0
    tip_local_cl = right_side[-1].local_cl if right_side else 0.0
    max_station = max(stations_out, key=lambda s: s.local_cl)
    max_local_cl = max_station.local_cl
    max_local_cl_location = max_station.span_location

    return ClDistributionResult(
        stations=stations_out,
        root_local_cl=root_local_cl,
        tip_local_cl=tip_local_cl,
        max_local_cl=max_local_cl,
        max_local_cl_location=max_local_cl_location,
        avg_over_max_cl_ratio=safe_div(cl_input.target_cl, max_local_cl),
        solved_root_aoa_deg=math.degrees(alpha_root),
        total_cl_check=total_cl_check,
    )
