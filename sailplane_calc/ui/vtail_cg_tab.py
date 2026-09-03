from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QVBoxLayout, QWidget

from . import units as units_module
from .app_state import AppState
from .balance_diagram_widget import BalanceDiagramWidget
from .balance_point_box import BalancePointBox
from .widgets import add_result_row, make_spin


class VTailCGTab(QWidget):
    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        root = QVBoxLayout(self)

        settings = QGroupBox("Neutral Point Settings")
        sform = QFormLayout(settings)
        sform.addRow(
            "Stabilizer Efficiency (~0.9 T-tail, ~0.6 cruciform)",
            make_spin(state.vtail_stab_efficiency, self._bind("vtail_stab_efficiency"), decimals=2, step=0.05, minimum=0, maximum=2),
        )
        self.lbl_h_equiv = add_result_row(sform, "Equivalent Horizontal Stab Area")
        self.lbl_v_equiv = add_result_row(sform, "Equivalent Vertical Stab Area")
        root.addWidget(settings)

        self.balance_box = BalancePointBox(
            get_mode=lambda: state.vtail_balance_mode,
            on_mode_change=self._on_mode_change,
            get_value=lambda: state.vtail_balance_value,
            set_value=lambda v: setattr(state, "vtail_balance_value", v),
            get_units=lambda: state.units,
            notify=state.notify,
        )
        root.addWidget(self.balance_box)

        diagram_box = QGroupBox("Balance Diagram")
        diagram_layout = QVBoxLayout(diagram_box)
        self.diagram = BalanceDiagramWidget(lambda: state.units)
        diagram_layout.addWidget(self.diagram)
        root.addWidget(diagram_box)
        root.addStretch(1)

        state.changed.connect(self.refresh)
        self.refresh()

    def _bind(self, attr: str):
        def _on_change(value: float) -> None:
            setattr(self.state, attr, value)
            self.state.notify()

        return _on_change

    def _on_mode_change(self, mode: str) -> None:
        self.state.switch_balance_mode("vtail", mode)
        self.state.notify()

    def refresh(self) -> None:
        u = self.state.units
        area_label = units_module.unit_label(u, "area")
        equivalent = self.state.vtail_equivalent_areas()
        h_area = units_module.to_display(equivalent.horizontal_area, u, "area")
        v_area = units_module.to_display(equivalent.vertical_area, u, "area")
        self.lbl_h_equiv.setText(f"{h_area:.2f} {area_label}")
        self.lbl_v_equiv.setText(f"{v_area:.2f} {area_label}")

        np_result = self.state.neutral_point_vtail()
        balance = self.state.balance_point_vtail()
        self.balance_box.refresh(np_result, balance)

        wing = self.state.wing_result()
        self.diagram.set_data(
            wing.root_chord,
            wing.surface.point_0,
            wing.surface.mac_length,
            np_result.neutral_point_from_root_le,
            balance.cg_from_root_le,
        )
