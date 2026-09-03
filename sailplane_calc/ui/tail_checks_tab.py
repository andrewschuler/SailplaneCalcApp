from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .app_state import AppState
from .widgets import make_spin

_CL_THERM_HINT = "0.7 big glider, 0.6 DLG size"

# (result attribute, row label, value format, suggested range, what it does, affected by) --
# text reproduced from the reference workbook's own Tail Sizing Checks sheet (its "Suggested
# Sizes" / "What it does?" / "What affects the results" columns), same row order.
_METRICS = [
    (
        "spiral_stability_b",
        "Spiral Stability (b)",
        "{:.2f}",
        ">5 Stable / =5 Neutral / <5 Unstable\n\n"
        "4.0-6.0 Polyhedral Glider\n2.0-5.0 Aileron Thermal Duration Glider\n\n"
        "Mark Drela recommends:\n5.0-5.5 Polyhedral Glider\n>3.0 Aileron TD Glider",
        "The dihedral angle of the wing provides some degree of natural spiral stability. A "
        "spirally-unstable aircraft tends to constantly increase its bank angle at some rate, "
        "and therefore requires constant attention by the pilot. Conversely, a spirally-stable "
        "aircraft will tend to roll upright with no control input from the pilot, and thus "
        "make the aircraft easier to fly.",
        "CL Therm and EDA on this tab, Vertical Tail Area, and Vertical Stabilizer moment and "
        "Main Wing span on the Wing tab.",
    ),
    (
        "tail_volume_h",
        "Horizontal Tail Volume (Vh)",
        "{:.3f}",
        "0.3-0.6\n\nMark Drela recommends:\n0.4-0.45 Polyhedral Glider\n0.3-0.6 Aileron TD Glider",
        "A measure of the effectiveness of the horizontal tail. The Neutral Point location is "
        "primarily controlled by the size of the horizontal tail and its moment arm from the CG.",
        "Horizontal tail area, main wing area, horizontal tail arm, and main wing chord on the "
        "Wing tab.",
    ),
    (
        "tail_volume_v",
        "Vertical Tail Volume (Vv)",
        "{:.3f}",
        "0.02-0.04 Polyhedral Glider\n0.015-0.025 Aileron Thermal Duration Glider\n"
        "0.05-0.06 Discus Launch Glider\n\n"
        "Mark Drela recommends:\n>0.03 Polyhedral Glider\n>0.025 Aileron TD Glider",
        "The primary role of the vertical tail is to provide yaw damping, the tendency of yaw "
        "oscillations of the aircraft to subside. The vertical tail also provides yaw "
        "stability, though this is almost certainly ensured if the yaw damping is sufficient.",
        "Vertical tail area, main wing area, vertical tail arm, and main wing span on the Wing "
        "tab.",
    ),
    (
        "roll_control_vvb",
        "Dihedral Sizing - Roll Control (VvB)",
        "{:.3f}",
        "0.10 = Marginal Roll Control\n0.20 = Very Effective Roll Control",
        "On rudder/elevator aircraft, the rudder acts to generate a sideslip angle, which then "
        "combines with dihedral to generate a roll moment and thus provide roll control.",
        "Spiral Stability (b) and Equivalent Dihedral Angle (EDA) on this tab.",
    ),
    (
        "eda_deg",
        "Equivalent Dihedral Angle (EDA)",
        "{:.2f}",
        "12 for a Polyhedral Glider\n6 for an Aileron Thermal Duration Glider",
        "EDA is a major factor in roll response, roll rate, and spiral stability. For a "
        "rudder-and-elevator model at a given airspeed and yaw angle, the steady-state roll "
        "rate will be proportional to EDA.",
        "Main wing dihedral and main wing span on the Wing tab.",
    ),
]

_COLUMNS = ["Metric", "Value", "Suggested Range", "What It Does", "Affected By"]


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
        cl_hint = QLabel(_CL_THERM_HINT)
        cl_hint.setStyleSheet("color: #888;")
        sform.addRow("", cl_hint)
        root.addWidget(settings)

        self.cruciform_box, self.cruciform_table, self.cruciform_value_items = self._results_box(
            "Cruciform Tail"
        )
        self.vtail_box, self.vtail_table, self.vtail_value_items = self._results_box("V-Tail")
        root.addWidget(self.cruciform_box)
        root.addWidget(self.vtail_box)

        state.changed.connect(self.refresh)
        self.refresh()

    @staticmethod
    def _results_box(title: str):
        box = QGroupBox(title)
        layout = QVBoxLayout(box)

        table = QTableWidget(len(_METRICS), len(_COLUMNS))
        table.setHorizontalHeaderLabels(_COLUMNS)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setWordWrap(True)
        # Fixed (not Stretch) widths: row heights are computed from these immediately below,
        # before the table has ever been shown/laid out -- a Stretch column's real width isn't
        # known until then, which would make resizeRowsToContents() wrap against a stale
        # (usually far too narrow) width and leave every row far taller than its text needs.
        for col, width in enumerate([160, 70, 220, 380, 280]):
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
            table.setColumnWidth(col, width)

        value_items: list[QTableWidgetItem] = []
        for row, (_attr, label, _fmt, suggested, what_it_does, affected_by) in enumerate(_METRICS):
            table.setItem(row, 0, QTableWidgetItem(label))
            value_item = QTableWidgetItem("--")
            value_items.append(value_item)
            table.setItem(row, 1, value_item)
            table.setItem(row, 2, QTableWidgetItem(suggested))
            table.setItem(row, 3, QTableWidgetItem(what_it_does))
            table.setItem(row, 4, QTableWidgetItem(affected_by))

        table.resizeRowsToContents()
        layout.addWidget(table)
        return box, table, value_items

    def _bind(self, attr: str):
        def _on_change(value: float) -> None:
            setattr(self.state, attr, value)
            self.state.notify()

        return _on_change

    @staticmethod
    def _fill(result, value_items: list[QTableWidgetItem]) -> None:
        for item, (attr, _label, fmt, *_rest) in zip(value_items, _METRICS):
            item.setText(fmt.format(getattr(result, attr)))

    def refresh(self) -> None:
        self._fill(self.state.tail_checks_cruciform(), self.cruciform_value_items)
        self._fill(self.state.tail_checks_vtail(), self.vtail_value_items)
        self.cruciform_table.resizeRowsToContents()
        self.vtail_table.resizeRowsToContents()

        self.cruciform_box.setVisible(self.state.tail_type == "cruciform")
        self.vtail_box.setVisible(self.state.tail_type == "vtail")
