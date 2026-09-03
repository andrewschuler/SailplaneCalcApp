"""V-Tail tab: a single mirrored panel plus its dihedral (the included angle between the V's)."""
from __future__ import annotations

import math

from .geometry import compute_surface
from .models import PanelInput, VTailConvertResult, VTailGeometryResult


def compute_vtail(panel: PanelInput, dihedral_rise: float) -> VTailGeometryResult:
    surface = compute_surface([panel], mirrored=True)

    # The panel's own span is its physical/slant length (a ruler measurement along the
    # panel, like the Wing tab's own panel spans), with dihedral_rise the vertical rise over
    # that length -- so half_dihedral = asin(rise/span), the same relationship
    # wing.compute_panel_dihedral_deg uses for the main wing's dihedral, not atan (confirmed
    # against the reference workbook's V-Tail sheet, which computes this via ASIN). The ratio
    # is clamped to [-1, 1] before asin for the same reason wing.py clamps it: a rise larger
    # in magnitude than the span is physically extreme but reachable mid-edit.
    if panel.span > 0:
        ratio = max(-1.0, min(1.0, dihedral_rise / panel.span))
        half_dihedral_deg = math.degrees(math.asin(ratio))
    else:
        half_dihedral_deg = 0.0
    total_angle_deg = 180.0 - 2 * half_dihedral_deg

    return VTailGeometryResult(
        surface=surface,
        half_dihedral_deg=half_dihedral_deg,
        total_angle_deg=total_angle_deg,
    )


def compute_vtail_equivalent_areas(vtail: VTailGeometryResult) -> VTailConvertResult:
    """The horizontal/vertical stabilizer areas this V-tail panel is aerodynamically
    equivalent to, for feeding into the same neutral-point/tail-checks formulas a cruciform
    tail's horizontal stabilizer and vertical fin areas do: a cos^2/sin^2 split of the
    V-tail's own total physical area by its dihedral angle (confirmed against the reference
    workbook's Balance Point sheet). This is a different relationship from
    `vtail_convert.vtail_to_conventional`'s tangent-based split, which is a separate, standalone
    "what-if" conversion tool (the Quick V-Tail Sizing tab) -- not a source of these areas.
    """
    theta = math.radians(vtail.half_dihedral_deg)
    total_area = vtail.surface.total_area
    horizontal_area = total_area * math.cos(theta) ** 2
    vertical_area = total_area * math.sin(theta) ** 2
    return VTailConvertResult(horizontal_area=horizontal_area, vertical_area=vertical_area)
