"""Display-unit conversion layer.

The engine always works in inches/oz/mph internally (see engine module docstrings) --
metric is purely a UI-boundary concern: convert to canonical units on input, convert back
for display. Every geometry/ratio formula is unit-agnostic, so only length, weight, speed,
area, and wing loading need conversion at all.
"""
from __future__ import annotations

from enum import Enum

MM_PER_INCH = 25.4
G_PER_OZ = 28.349523125
KPH_PER_MPH = 1.609344
DM2_PER_IN2 = (MM_PER_INCH**2) / 10000  # 1 in^2 = 0.064516 dm^2


class Units(Enum):
    IMPERIAL = "imperial"
    METRIC = "metric"


def to_display(canonical_value: float, units: Units, kind: str) -> float:
    if units is Units.IMPERIAL:
        return canonical_value
    if kind == "length":
        return canonical_value * MM_PER_INCH
    if kind == "weight":
        return canonical_value * G_PER_OZ
    if kind == "speed":
        return canonical_value * KPH_PER_MPH
    if kind == "area":
        return canonical_value * DM2_PER_IN2
    raise ValueError(f"Unknown unit kind: {kind}")


def from_display(display_value: float, units: Units, kind: str) -> float:
    if units is Units.IMPERIAL:
        return display_value
    if kind == "length":
        return display_value / MM_PER_INCH
    if kind == "weight":
        return display_value / G_PER_OZ
    if kind == "speed":
        return display_value / KPH_PER_MPH
    if kind == "area":
        return display_value / DM2_PER_IN2
    raise ValueError(f"Unknown unit kind: {kind}")


_LABELS = {
    Units.IMPERIAL: {"length": "in", "weight": "oz", "speed": "mph", "area": "in²"},
    Units.METRIC: {"length": "mm", "weight": "g", "speed": "kph", "area": "dm²"},
}


def unit_label(units: Units, kind: str) -> str:
    return _LABELS[units][kind]


def wing_loading_to_display(weight_oz: float, area_in2: float, units: Units) -> float:
    if units is Units.IMPERIAL:
        return weight_oz / area_in2 * 144 if area_in2 else 0.0
    weight_g = to_display(weight_oz, Units.METRIC, "weight")
    area_dm2 = to_display(area_in2, Units.METRIC, "area")
    return weight_g / area_dm2 if area_dm2 else 0.0


def wing_loading_unit_label(units: Units) -> str:
    return "oz/ft²" if units is Units.IMPERIAL else "gr/dm²"
