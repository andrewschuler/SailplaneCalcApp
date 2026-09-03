from __future__ import annotations

from dataclasses import replace

from PySide6.QtWidgets import QFormLayout, QGroupBox, QHBoxLayout, QVBoxLayout, QWidget

from ..engine.planform import compute_fin_panels, compute_planform_panels
from . import units as units_module
from .app_state import AppState
from .planform_widget import PlanformWidget
from .widgets import UnitSpinBox, add_result_row


class CruciformTailTab(QWidget):
    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self._unit_spins: list[UnitSpinBox] = []
        root = QVBoxLayout(self)

        h_box = QGroupBox("Horizontal Stabilizer")
        h_form = QFormLayout(h_box)
        h_form.addRow("Root Chord", self._panel_row("stab_panel", "chord_root"))
        h_form.addRow("Tip Chord", self._panel_row("stab_panel", "chord_tip"))
        h_form.addRow("Span (half)", self._panel_row("stab_panel", "span"))
        h_form.addRow("Sweepback", self._panel_row("stab_panel", "sweep_offset"))
        h_form.addRow("Wing TE to Stab LE Gap", self._plain_row("gap_wing_te_to_stab_le"))
        self.h_span = add_result_row(h_form, "Total Span")
        self.h_area = add_result_row(h_form, "Total Area")
        self.h_mac = add_result_row(h_form, "Mean Chord (area/span)")
        self.h_mac_length = add_result_row(h_form, "Mean Aerodynamic Chord (length)")
        self.h_ar = add_result_row(h_form, "Aspect Ratio")
        self.h_taper = add_result_row(h_form, "Taper Ratio")
        self.h_sweep_angle = add_result_row(h_form, "Sweep Angle (LE)")
        self.h_pt25 = add_result_row(h_form, "25% MAC Point from Root LE")
        self.h_pct_wing = add_result_row(h_form, "% of Wing Area")
        self.h_planform = PlanformWidget(lambda: self.state.units)
        h_form.addRow(self.h_planform)

        v_box = QGroupBox("Vertical Stabilizer (fin)")
        v_form = QFormLayout(v_box)
        v_form.addRow("Center (Root) Chord", self._fin_root_row())
        v_form.addRow("Lower/Bottom Chord", self._panel_row("fin_lower", "chord_tip"))
        v_form.addRow("Lower Span", self._panel_row("fin_lower", "span"))
        v_form.addRow("Lower Sweepback", self._panel_row("fin_lower", "sweep_offset"))
        v_form.addRow("Upper/Top Chord", self._panel_row("fin_upper", "chord_tip"))
        v_form.addRow("Upper Span", self._panel_row("fin_upper", "span"))
        v_form.addRow("Upper Sweepback", self._panel_row("fin_upper", "sweep_offset"))
        v_form.addRow("Wing TE to Fin LE Gap", self._plain_row("gap_wing_te_to_fin_le"))
        self.v_span = add_result_row(v_form, "Total Span")
        self.v_area = add_result_row(v_form, "Total Area")
        self.v_mac = add_result_row(v_form, "Mean Chord (area/span)")
        self.v_mac_length = add_result_row(v_form, "Mean Aerodynamic Chord (length)")
        self.v_ar = add_result_row(v_form, "Aspect Ratio")
        self.v_taper = add_result_row(v_form, "Taper Ratio")
        self.v_taper_lower = add_result_row(v_form, "Taper Ratio (bottom panel)")
        self.v_taper_upper = add_result_row(v_form, "Taper Ratio (upper panel)")
        self.v_sweep_angle = add_result_row(v_form, "Sweep Angles (lower, upper)")
        self.v_pt25 = add_result_row(v_form, "25% MAC Point from Root LE")
        self.v_pct_wing = add_result_row(v_form, "% of Wing Area")
        self.v_planform = PlanformWidget(lambda: self.state.units, vertical=True)
        v_form.addRow(self.v_planform)

        row = QHBoxLayout()
        row.addWidget(h_box)
        row.addWidget(v_box)
        root.addLayout(row)
        root.addStretch(1)

        state.changed.connect(self.refresh)
        self.refresh()

    def _panel_row(self, panel_attr: str, field: str) -> UnitSpinBox:
        def getter() -> float:
            return getattr(getattr(self.state, panel_attr), field)

        def setter(value: float) -> None:
            panel = getattr(self.state, panel_attr)
            setattr(self.state, panel_attr, replace(panel, **{field: value}))

        spin = UnitSpinBox(self.state, getter, setter, "length")
        self._unit_spins.append(spin)
        return spin

    def _fin_root_row(self) -> UnitSpinBox:
        """Center chord drives both the lower and upper panels' shared root."""

        def setter(value: float) -> None:
            self.state.fin_lower = replace(self.state.fin_lower, chord_root=value)
            self.state.fin_upper = replace(self.state.fin_upper, chord_root=value)

        spin = UnitSpinBox(self.state, lambda: self.state.fin_lower.chord_root, setter, "length")
        self._unit_spins.append(spin)
        return spin

    def _plain_row(self, attr: str) -> UnitSpinBox:
        spin = UnitSpinBox(
            self.state, lambda: getattr(self.state, attr), lambda v: setattr(self.state, attr, v), "length"
        )
        self._unit_spins.append(spin)
        return spin

    def refresh(self) -> None:
        for spin in self._unit_spins:
            spin.sync()

        u = self.state.units
        length = units_module.unit_label(u, "length")
        area_label = units_module.unit_label(u, "area")

        def fmt_len(value: float) -> str:
            return f"{units_module.to_display(value, u, 'length'):.2f} {length}"

        def fmt_area(value: float) -> str:
            return f"{units_module.to_display(value, u, 'area'):.2f} {area_label}"

        wing_area = self.state.wing_result().surface.total_area

        h = self.state.horizontal_stab_surface()
        self.h_span.setText(fmt_len(h.total_span))
        self.h_area.setText(fmt_area(h.total_area))
        self.h_mac.setText(fmt_len(h.mean_chord))
        self.h_mac_length.setText(fmt_len(h.mac_length))
        self.h_ar.setText(f"{h.aspect_ratio:.2f}")
        self.h_taper.setText(f"{h.taper_ratio:.2f}")
        self.h_sweep_angle.setText(", ".join(f"{d:.1f}°" for d in h.panel_sweep_angle_deg))
        self.h_pt25.setText(fmt_len(h.point_25))
        self.h_pct_wing.setText(f"{h.total_area / wing_area * 100:.2f} %" if wing_area else "--")
        h_panels = compute_planform_panels([self.state.stab_panel], mirror=True)
        self.h_planform.set_data(h_panels, h.point_25, h.mac_span_location)

        v = self.state.vertical_fin_surface()
        self.v_span.setText(fmt_len(v.total_span))
        self.v_area.setText(fmt_area(v.total_area))
        self.v_mac.setText(fmt_len(v.mean_chord))
        self.v_mac_length.setText(fmt_len(v.mac_length))
        self.v_ar.setText(f"{v.aspect_ratio:.2f}")
        self.v_taper.setText(f"{v.taper_ratio:.2f}")
        lower_taper, upper_taper = self.state.vertical_fin_panel_taper_ratios()
        self.v_taper_lower.setText(f"{lower_taper:.2f}")
        self.v_taper_upper.setText(f"{upper_taper:.2f}")
        self.v_sweep_angle.setText(", ".join(f"{d:.1f}°" for d in v.panel_sweep_angle_deg))
        self.v_pt25.setText(fmt_len(v.point_25))
        self.v_pct_wing.setText(f"{v.total_area / wing_area * 100:.2f} %" if wing_area else "--")
        v_panels = compute_fin_panels(self.state.fin_lower, self.state.fin_upper)
        self.v_planform.set_data(v_panels, v.point_25, v.mac_span_location)
