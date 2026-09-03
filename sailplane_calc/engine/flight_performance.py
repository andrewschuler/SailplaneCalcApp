"""Stall-speed / lift-coefficient / G-load calculator (new in the metric reference workbook).

Implemented from the standard lift equation `L = Cl * 0.5 * rho * V^2 * S` at level flight
(`L = W`), using sea-level standard air density, rather than transliterating the reference
workbook's tangled unit-conversion chain -- independently cross-checked in SI units against
that workbook's own worked example (Cl ~= 0.77 for a 400g/35.28dm^2 model stalling at 17.5kph)
before adopting this cleaner form.

All inputs/outputs are in the engine's canonical units (inches, ounces, mph, dimensionless).
"""
from __future__ import annotations

import math

AIR_DENSITY_SLUG_PER_FT3 = 0.002378  # sea-level standard atmosphere
MAX_SPEED_MULTIPLIER = 4.0  # the reference workbook's fixed max-speed/stall-speed ratio


def _mph_to_fts(speed_mph: float) -> float:
    return speed_mph * 5280 / 3600


def _fts_to_mph(speed_fts: float) -> float:
    return speed_fts * 3600 / 5280


def cl_from_stall_speed(weight_oz: float, area_in2: float, stall_speed_mph: float) -> float:
    weight_lbf = weight_oz / 16
    area_ft2 = area_in2 / 144
    v_fts = _mph_to_fts(stall_speed_mph)
    denominator = 0.5 * AIR_DENSITY_SLUG_PER_FT3 * v_fts**2 * area_ft2
    return weight_lbf / denominator if denominator else 0.0


def stall_speed_from_cl(weight_oz: float, area_in2: float, cl: float) -> float:
    weight_lbf = weight_oz / 16
    area_ft2 = area_in2 / 144
    denominator = 0.5 * AIR_DENSITY_SLUG_PER_FT3 * cl * area_ft2
    # A non-positive Cl or area has no physical stall speed -- 0.0 rather than a domain
    # error keeps a mid-edit or config-loaded value from crashing every tab's refresh().
    if denominator <= 0:
        return 0.0
    return _fts_to_mph(math.sqrt(weight_lbf / denominator))


def g_load_at_speed(weight_oz: float, area_in2: float, cl: float, speed_mph: float) -> float:
    weight_lbf = weight_oz / 16
    area_ft2 = area_in2 / 144
    v_fts = _mph_to_fts(speed_mph)
    lift_lbf = cl * 0.5 * AIR_DENSITY_SLUG_PER_FT3 * v_fts**2 * area_ft2
    return lift_lbf / weight_lbf if weight_lbf else 0.0
