from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .app_state import AppState
from .widgets import add_result_row, make_spin


_HELP = (
    "Mark Drela's tail-sizing design checks. Suggested ranges:\n"
    "  b (spiral stability): >5 stable / =5 neutral / <5 unstable "
    "(5.0-5.5 poly glider, >3.0 aileron TD)\n"
    "  Vh (horiz. tail volume): 0.4-0.45 polyhedral, 0.3-0.6 aileron TD\n"
    "  Vv (vert. tail volume): >0.03 polyhedral, >0.025 aileron TD, 0.05-0.06 DLG"
)


class TailChecksTab(QWidget):
    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        root = QVBoxLayout(self)

        settings = QGroupBox("Settings")
        sform = QFormLayout(settings)
        sform.addRow(
            "Assumed CL during slow thermalling",
            make_spin(state.cl_therm, self._bind("cl_therm"), decimals=2, step=0.05, minimum=0.01, maximum=2),
        )
        root.addWidget(settings)

        row = QHBoxLayout()
        self.cruciform_box, self.cruciform_labels = self._results_box("Cruciform Tail")
        self.vtail_box, self.vtail_labels = self._results_box("V-Tail")
        row.addWidget(self.cruciform_box)
        row.addWidget(self.vtail_box)
        root.addLayout(row)

        help_label = QLabel(_HELP)
        help_label.setWordWrap(True)
        root.addWidget(help_label)
        root.addStretch(1)

        state.changed.connect(self.refresh)
        self.refresh()

    @staticmethod
    def _results_box(title: str):
        box = QGroupBox(title)
        form = QFormLayout(box)
        labels = {
            "eda": add_result_row(form, "Equivalent Dihedral Angle (deg)"),
            "b": add_result_row(form, "Spiral Stability (b)"),
            "vh": add_result_row(form, "Horizontal Tail Volume (Vh)"),
            "vv": add_result_row(form, "Vertical Tail Volume (Vv)"),
        }
        return box, labels

    def _bind(self, attr: str):
        def _on_change(value: float) -> None:
            setattr(self.state, attr, value)
            self.state.notify()

        return _on_change

    def refresh(self) -> None:
        cruciform = self.state.tail_checks_cruciform()
        self.cruciform_labels["eda"].setText(f"{cruciform.eda_deg:.2f}")
        self.cruciform_labels["b"].setText(f"{cruciform.spiral_stability_b:.2f}")
        self.cruciform_labels["vh"].setText(f"{cruciform.tail_volume_h:.3f}")
        self.cruciform_labels["vv"].setText(f"{cruciform.tail_volume_v:.3f}")

        vtail = self.state.tail_checks_vtail()
        self.vtail_labels["eda"].setText(f"{vtail.eda_deg:.2f}")
        self.vtail_labels["b"].setText(f"{vtail.spiral_stability_b:.2f}")
        self.vtail_labels["vh"].setText(f"{vtail.tail_volume_h:.3f}")
        self.vtail_labels["vv"].setText(f"{vtail.tail_volume_v:.3f}")

        self.cruciform_box.setVisible(self.state.tail_type == "cruciform")
        self.vtail_box.setVisible(self.state.tail_type == "vtail")
