from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QVBoxLayout, QWidget

from .app_state import AppState
from .balance_diagram_widget import BalanceDiagramWidget
from .balance_point_box import BalancePointBox
from .widgets import make_spin


class CruciformCGTab(QWidget):
    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        root = QVBoxLayout(self)

        settings = QGroupBox("Neutral Point Settings")
        sform = QFormLayout(settings)
        sform.addRow(
            "Stabilizer Efficiency (~0.9 T-tail, ~0.6 cruciform)",
            make_spin(state.cruciform_stab_efficiency, self._bind("cruciform_stab_efficiency"), decimals=2, step=0.05, minimum=0, maximum=2),
        )
        root.addWidget(settings)

        self.balance_box = BalancePointBox(
            get_mode=lambda: state.cruciform_balance_mode,
            on_mode_change=self._on_mode_change,
            get_value=lambda: state.cruciform_balance_value,
            set_value=lambda v: setattr(state, "cruciform_balance_value", v),
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
        self.state.switch_balance_mode("cruciform", mode)
        self.state.notify()

    def refresh(self) -> None:
        np_result = self.state.neutral_point_cruciform()
        balance = self.state.balance_point_cruciform()
        self.balance_box.refresh(np_result, balance)

        wing = self.state.wing_result()
        self.diagram.set_data(
            wing.root_chord,
            wing.surface.point_0,
            wing.surface.mac_length,
            np_result.neutral_point_from_root_le,
            balance.cg_from_root_le,
        )
