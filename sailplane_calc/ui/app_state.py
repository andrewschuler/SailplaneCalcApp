"""Central input store shared by all tabs, replacing Excel's implicit cross-sheet cell refs.

Defaults are the workbook's own worked example (120" wing, 102 sq-in stab, etc.) so a fresh
launch already reproduces the numbers documented in SailplaneCalc.xls -- an easy sanity check
that the port is faithful.
"""
from __future__ import annotations

from dataclasses import replace as dataclass_replace

from PySide6.QtCore import QObject, Signal

from ..engine import flight_performance
from ..engine.models import PanelInput, TailMount, WingInput, WingPanelInput
from ..engine.neutral_point import (
    compute_balance_point,
    compute_neutral_point_cruciform,
    compute_neutral_point_vtail,
)
from ..engine.tail_checks import compute_tail_checks
from ..engine.tail_cruciform import compute_horizontal_stab, compute_vertical_fin
from ..engine.tail_vtail import compute_vtail
from ..engine.vtail_convert import conventional_to_vtail, vtail_to_conventional
from ..engine.wing import compute_dihedral_rise_from_angles, compute_wing
from .units import Units


class AppState(QObject):
    changed = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.units = Units.IMPERIAL
        self.tail_type = "cruciform"  # "cruciform" | "vtail" -- which tabs Setup shows

        self.weight_oz = 31.0
        self.estimated_speed_mph = 20.0

        # Chords are stored as N+1 breakpoints (root, panel1..4 tip) so a panel's root always
        # equals the previous panel's tip -- the wing can't have a physically discontinuous
        # chord, matching how the workbook reuses D14/G14/... as both a tip and the next
        # panel's root. The 4th panel defaults to unused (span4=0).
        self.chord_root = 10.5
        self.chord1_tip = 10.0
        self.chord2_tip = 8.0
        self.chord3_tip = 5.0
        self.chord4_tip = 0.0
        self.span1, self.span2, self.span3, self.span4 = 18.0, 24.0, 18.0, 0.0
        self.sweep1, self.sweep2, self.sweep3, self.sweep4 = 0.0, 0.8, 1.0, 0.0
        self.rise1, self.rise2, self.rise3, self.rise4 = 0.0, 4.25, 10.4, 0.0

        # Speed / Cl / G-load calculator: mode picks whether "speed_calc_value" holds a stall
        # speed (mph) or a Cl, mirroring the balance-point selector pattern below.
        self.speed_calc_mode = "stall_speed"
        self.speed_calc_value = 15.0

        self.gap_wing_te_to_stab_le = 27.0
        self.gap_wing_te_to_fin_le = 32.75

        self.stab_panel = PanelInput(span=12, chord_root=5.5, chord_tip=3, sweep_offset=1.8)
        self.fin_lower = PanelInput(span=3.5, chord_root=7, chord_tip=5, sweep_offset=1)
        self.fin_upper = PanelInput(span=10.5, chord_root=7, chord_tip=3, sweep_offset=1.5)
        self.cruciform_stab_efficiency = 0.60

        self.vtail_panel = PanelInput(span=20.65, chord_root=5.5, chord_tip=3, sweep_offset=0.86)
        self.vtail_dihedral_rise = 14.9
        self.vtail_stab_efficiency = 0.60

        self.cl_therm = 0.6

        # Which of the three mutually-derivable balance-point views is the "input" for each
        # CG tab (see compute_balance_point) -- one of "static_margin", "cg_pct", "cg_distance".
        self.cruciform_balance_mode = "static_margin"
        self.cruciform_balance_value = 6.3
        self.vtail_balance_mode = "static_margin"
        self.vtail_balance_value = 10.0

        # Quick V-Tail Sizing tab's two independent conversion sections.
        self.qv_horizontal_area = 102.00
        self.qv_vertical_area = 73.50
        self.qv_v_half_area = 87.75

    def notify(self) -> None:
        self.changed.emit()

    # --- derived results -------------------------------------------------

    def wing_panels(self) -> list[WingPanelInput]:
        return [
            WingPanelInput(self.span1, self.chord_root, self.chord1_tip, self.sweep1, self.rise1),
            WingPanelInput(self.span2, self.chord1_tip, self.chord2_tip, self.sweep2, self.rise2),
            WingPanelInput(self.span3, self.chord2_tip, self.chord3_tip, self.sweep3, self.rise3),
            WingPanelInput(self.span4, self.chord3_tip, self.chord4_tip, self.sweep4, self.rise4),
        ]

    def wing_input(self) -> WingInput:
        return WingInput(
            weight_oz=self.weight_oz,
            panels=self.wing_panels(),
            estimated_speed_mph=self.estimated_speed_mph,
        )

    def wing_result(self):
        return compute_wing(self.wing_input())

    def horizontal_stab_surface(self):
        return compute_horizontal_stab(self.stab_panel)

    def vertical_fin_surface(self):
        return compute_vertical_fin(self.fin_lower, self.fin_upper)

    def vtail_geometry(self):
        return compute_vtail(self.vtail_panel, self.vtail_dihedral_rise)

    def vtail_equivalent_areas(self):
        vtail = self.vtail_geometry()
        return vtail_to_conventional(
            v_half_area=vtail.surface.panel_areas[0] if vtail.surface.panel_areas else 0.0,
            half_dihedral_deg=vtail.half_dihedral_deg,
        )

    def neutral_point_cruciform(self):
        return compute_neutral_point_cruciform(
            self.wing_result(),
            self.horizontal_stab_surface(),
            gap_wing_te_to_stab_le=self.gap_wing_te_to_stab_le,
            stab_efficiency=self.cruciform_stab_efficiency,
        )

    def neutral_point_vtail(self):
        vtail = self.vtail_geometry()
        equivalent = self.vtail_equivalent_areas()
        return compute_neutral_point_vtail(
            self.wing_result(),
            vtail,
            horizontal_equivalent_area=equivalent.horizontal_area,
            gap_wing_te_to_vtail_le=self.gap_wing_te_to_stab_le,
            stab_efficiency=self.vtail_stab_efficiency,
        )

    _BALANCE_KWARG = {
        "static_margin": "static_margin_pct",
        "cg_pct": "cg_pct_mac",
        "cg_distance": "cg_from_root_le",
    }

    def balance_point_cruciform(self):
        kwarg = self._BALANCE_KWARG[self.cruciform_balance_mode]
        return compute_balance_point(
            self.wing_result(), self.neutral_point_cruciform(), **{kwarg: self.cruciform_balance_value}
        )

    def balance_point_vtail(self):
        kwarg = self._BALANCE_KWARG[self.vtail_balance_mode]
        return compute_balance_point(
            self.wing_result(), self.neutral_point_vtail(), **{kwarg: self.vtail_balance_value}
        )

    def switch_balance_mode(self, which: str, new_mode: str) -> None:
        """Recomputes the stored value so the physical balance point (CG location) stays
        the same when switching *how* it's specified -- rather than reinterpreting the old
        raw number under the new mode's units, which is the trap the original workbook falls
        into when a formula cell gets overwritten with a plain number."""
        if which == "cruciform":
            bp = self.balance_point_cruciform()
            mode_attr, value_attr = "cruciform_balance_mode", "cruciform_balance_value"
        else:
            bp = self.balance_point_vtail()
            mode_attr, value_attr = "vtail_balance_mode", "vtail_balance_value"
        value = {
            "static_margin": bp.static_margin_pct,
            "cg_pct": bp.cg_pct_mac,
            "cg_distance": bp.cg_from_root_le,
        }[new_mode]
        setattr(self, value_attr, value)
        setattr(self, mode_attr, new_mode)

    def tail_checks_cruciform(self):
        horizontal = TailMount(self.horizontal_stab_surface(), self.gap_wing_te_to_stab_le)
        vertical = TailMount(self.vertical_fin_surface(), self.gap_wing_te_to_fin_le)
        return compute_tail_checks(
            self.wing_input(), self.wing_result(), horizontal, vertical, self.cl_therm
        )

    def tail_checks_vtail(self):
        vtail = self.vtail_geometry()
        equivalent = self.vtail_equivalent_areas()
        horizontal = TailMount(
            surface=self._replace_area(vtail.surface, equivalent.horizontal_area),
            gap_wing_te_to_surface_le=self.gap_wing_te_to_stab_le,
        )
        vertical = TailMount(
            surface=self._replace_area(vtail.surface, equivalent.vertical_area),
            gap_wing_te_to_surface_le=self.gap_wing_te_to_fin_le,
        )
        return compute_tail_checks(
            self.wing_input(), self.wing_result(), horizontal, vertical, self.cl_therm
        )

    @staticmethod
    def _replace_area(surface, area: float):
        return dataclass_replace(surface, total_area=area)

    def quick_conventional_to_vtail(self):
        return conventional_to_vtail(self.qv_horizontal_area, self.qv_vertical_area)

    def quick_vtail_to_conventional(self):
        half_dihedral_deg = self.vtail_geometry().half_dihedral_deg
        return vtail_to_conventional(self.qv_v_half_area, half_dihedral_deg)

    def speed_performance(self):
        """Returns (cl, stall_speed_mph, max_speed_mph, g_load_at_max_speed)."""
        weight_oz = self.weight_oz
        area_in2 = self.wing_result().surface.total_area
        if self.speed_calc_mode == "stall_speed":
            stall_speed_mph = self.speed_calc_value
            cl = flight_performance.cl_from_stall_speed(weight_oz, area_in2, stall_speed_mph)
        else:
            cl = self.speed_calc_value
            stall_speed_mph = flight_performance.stall_speed_from_cl(weight_oz, area_in2, cl)
        max_speed_mph = stall_speed_mph * flight_performance.MAX_SPEED_MULTIPLIER
        g_load = flight_performance.g_load_at_speed(weight_oz, area_in2, cl, max_speed_mph)
        return cl, stall_speed_mph, max_speed_mph, g_load

    def dihedral_converter_rises(self, angles_deg: list[float]) -> list[float]:
        spans = [self.span1, self.span2, self.span3, self.span4]
        return compute_dihedral_rise_from_angles(spans, angles_deg)
