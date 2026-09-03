from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from . import units as units_module
from .app_state import AppState
from .widgets import UnitSpinBox, add_result_row


class QuickVTailTab(QWidget):
    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self._unit_spins: list[UnitSpinBox] = []
        root = QVBoxLayout(self)

        to_v = QGroupBox("Conventional → V-Tail")
        to_v_form = QFormLayout(to_v)
        to_v_form.addRow("Horizontal Stabilizer Area", self._area_row("qv_horizontal_area"))
        to_v_form.addRow("Vertical Stabilizer Area", self._area_row("qv_vertical_area"))
        self.lbl_v_half = add_result_row(to_v_form, "V-Tail Area (each half)")
        self.lbl_dihedral = add_result_row(to_v_form, "Dihedral from Horizontal (deg)")
        self.lbl_angle = add_result_row(to_v_form, "Angle Between V's (deg)")

        to_conv = QGroupBox("V-Tail → Conventional")
        to_conv_form = QFormLayout(to_conv)
        to_conv_form.addRow("Area for one V half", self._area_row("qv_v_half_area"))
        to_conv_form.addRow(QLabel("Uses the dihedral from the V-Tail tab."))
        self.lbl_h_area = add_result_row(to_conv_form, "Horizontal Stabilizer Area")
        self.lbl_v_area = add_result_row(to_conv_form, "Vertical Stabilizer Area")

        row = QHBoxLayout()
        row.addWidget(to_v)
        row.addWidget(to_conv)
        root.addLayout(row)
        root.addStretch(1)

        state.changed.connect(self.refresh)
        self.refresh()

    def _area_row(self, attr: str) -> UnitSpinBox:
        spin = UnitSpinBox(
            self.state, lambda: getattr(self.state, attr), lambda v: setattr(self.state, attr, v), "area"
        )
        self._unit_spins.append(spin)
        return spin

    def refresh(self) -> None:
        for spin in self._unit_spins:
            spin.sync()

        u = self.state.units
        area_label = units_module.unit_label(u, "area")

        def fmt(value: float) -> str:
            return f"{units_module.to_display(value, u, 'area'):.2f} {area_label}"

        forward = self.state.quick_conventional_to_vtail()
        self.lbl_v_half.setText(fmt(forward.v_half_area))
        self.lbl_dihedral.setText(f"{forward.half_dihedral_deg:.2f}")
        self.lbl_angle.setText(f"{forward.total_angle_deg:.2f}")

        back = self.state.quick_vtail_to_conventional()
        self.lbl_h_area.setText(fmt(back.horizontal_area))
        self.lbl_v_area.setText(fmt(back.vertical_area))
