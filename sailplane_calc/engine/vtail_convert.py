"""Quick V-Tail Sizing tab: bidirectional area conversion between a conventional
(cruciform) tail and a V-tail of equivalent total area."""
from __future__ import annotations

import math

from .models import ConventionalToVTailResult, VTailConvertResult


def conventional_to_vtail(horizontal_area: float, vertical_area: float) -> ConventionalToVTailResult:
    v_half_area = (horizontal_area + vertical_area) / 2
    # atan2 (not atan(vertical/horizontal)) so a zero horizontal area -- reachable by just
    # clearing that input field -- gives a well-defined 90 degrees instead of crashing.
    half_dihedral_deg = math.degrees(math.atan2(vertical_area, horizontal_area))
    total_angle_deg = 180.0 - 2 * half_dihedral_deg
    return ConventionalToVTailResult(
        v_half_area=v_half_area,
        half_dihedral_deg=half_dihedral_deg,
        total_angle_deg=total_angle_deg,
    )


def vtail_to_conventional(v_half_area: float, half_dihedral_deg: float) -> VTailConvertResult:
    theta = math.radians(half_dihedral_deg)
    denominator = 1 + math.tan(theta)
    # denominator approaches 0 near a -45 degree dihedral -- reachable from a negative
    # dihedral rise roughly equal to -span -- which would otherwise divide by (near) zero
    # and blow up to an astronomical, meaningless area instead of cleanly raising.
    if abs(denominator) < 1e-9:
        return VTailConvertResult(horizontal_area=0.0, vertical_area=0.0)
    horizontal_area = v_half_area * 2 / denominator
    vertical_area = horizontal_area * math.tan(theta)
    return VTailConvertResult(horizontal_area=horizontal_area, vertical_area=vertical_area)
