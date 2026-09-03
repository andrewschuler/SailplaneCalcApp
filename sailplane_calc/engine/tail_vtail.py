"""V-Tail tab: a single mirrored panel plus its dihedral (the included angle between the V's)."""
from __future__ import annotations

import math
from dataclasses import replace

from .geometry import compute_surface, panel_25pct_from_own_root
from .models import PanelInput, VTailGeometryResult


def compute_vtail(panel: PanelInput, dihedral_rise: float) -> VTailGeometryResult:
    surface = compute_surface([panel], mirrored=True)

    half_dihedral_deg = (
        math.degrees(math.atan(dihedral_rise / panel.span)) if panel.span > 0 else 0.0
    )
    total_angle_deg = 180.0 - 2 * half_dihedral_deg

    # NOTE: the original workbook's V-Tail!D31 ("Location of 25% point") divides by the
    # panel's own area (D29) instead of the surface's total area (D24), e.g.
    # `=D29*D30/D29*2-D25*0.25`. That self-cancels to `2*x1 - 0.25*mean_chord`, which is NOT
    # the same value the general aggregation formula (used by Wing and the horizontal
    # stabilizer) would produce. Reproduced deliberately -- it's what the original tool's
    # downstream V-Tail neutral-point and tail-check calculations actually consumed. The
    # `mean_chord*0.25` term is upgraded to `mac_length*0.25` for consistency with the MAC
    # refinement adopted everywhere else (see geometry.compute_surface) -- there's no V-Tail
    # sheet in the newer reference workbook to confirm this against, but using the true MAC
    # here rather than area/span is the same improvement applied uniformly.
    x1 = panel_25pct_from_own_root(panel.chord_root, panel.chord_tip, panel.sweep_offset)
    point_25 = x1 * 2 - surface.mac_length * 0.25
    point_0 = point_25 - surface.mac_length * 0.25
    surface = replace(surface, point_0=point_0, point_25=point_25)

    return VTailGeometryResult(
        surface=surface,
        half_dihedral_deg=half_dihedral_deg,
        total_angle_deg=total_angle_deg,
    )
