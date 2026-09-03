from __future__ import annotations

from dataclasses import replace

from PySide6.QtWidgets import QFormLayout, QGroupBox, QVBoxLayout, QWidget

from ..engine.planform import compute_planform_panels
from . import units as units_module
from .app_state import AppState
from .planform_widget import PlanformWidget
from .widgets import UnitSpinBox, add_result_row


class VTailTab(QWidget):
    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self._unit_spins: list[UnitSpinBox] = []
        root = QVBoxLayout(self)

        box = QGroupBox("V-Tail Panel")
        form = QFormLayout(box)
        form.addRow("Root Chord", self._panel_row("chord_root"))
        form.addRow("Tip Chord", self._panel_row("chord_tip"))
        form.addRow("Span (half)", self._panel_row("span"))
        form.addRow("Sweepback", self._panel_row("sweep_offset"))
        form.addRow("Dihedral (rise)", self._plain_row("vtail_dihedral_rise"))
        form.addRow("Wing TE to V-Tail LE Gap", self._plain_row("gap_wing_te_to_vtail_le"))
        root.addWidget(box)

        results = QGroupBox("Total V-Tail Results")
        rform = QFormLayout(results)
        self.lbl_span = add_result_row(rform, "Total Span")
        self.lbl_area = add_result_row(rform, "Total Area")
        self.lbl_mac = add_result_row(rform, "Mean Chord (area/span)")
        self.lbl_ar = add_result_row(rform, "Aspect Ratio")
        self.lbl_half_dihedral = add_result_row(rform, "Dihedral from Horizontal (deg)")
        self.lbl_total_angle = add_result_row(rform, "Included Angle Between V's (deg)")
        root.addWidget(results)

        planform_box = QGroupBox("Planform")
        planform_layout = QVBoxLayout(planform_box)
        self.planform = PlanformWidget(lambda: self.state.units)
        planform_layout.addWidget(self.planform)
        root.addWidget(planform_box)
        root.addStretch(1)

        state.changed.connect(self.refresh)
        self.refresh()

    def _panel_row(self, field: str) -> UnitSpinBox:
        spin = UnitSpinBox(
            self.state,
            lambda: getattr(self.state.vtail_panel, field),
            lambda v: setattr(self.state, "vtail_panel", replace(self.state.vtail_panel, **{field: v})),
            "length",
        )
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

        vtail = self.state.vtail_geometry()
        s = vtail.surface
        self.lbl_span.setText(f"{units_module.to_display(s.total_span, u, 'length'):.2f} {length}")
        self.lbl_area.setText(f"{units_module.to_display(s.total_area, u, 'area'):.2f} {units_module.unit_label(u, 'area')}")
        self.lbl_mac.setText(f"{units_module.to_display(s.mean_chord, u, 'length'):.2f} {length}")
        self.lbl_ar.setText(f"{s.aspect_ratio:.2f}")
        self.lbl_half_dihedral.setText(f"{vtail.half_dihedral_deg:.1f}")
        self.lbl_total_angle.setText(f"{vtail.total_angle_deg:.1f}")

        panels = compute_planform_panels([self.state.vtail_panel], mirror=True)
        self.planform.set_data(panels, s.point_25, s.mac_span_location)
