"""Cl Calcs tab: local Cl distribution and lift-distribution-vs-ellipse curves for the wing,
from the horseshoe-vortex VLM in engine/cl_distribution.py. See AppState.cl_distribution_result().
"""
from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFormLayout, QGroupBox, QVBoxLayout, QWidget

from . import units as units_module
from .app_state import AppState
from .widgets import add_result_row
from .xy_chart_widget import ChartSeries, XYChartWidget

_LOCAL_CL_COLOR = QColor("#5a9fd4")
_LIFT_COLOR = QColor("#4fbf8f")
_ELLIPSE_COLOR = QColor("#d4a55a")


class ClCalcsTab(QWidget):
    def __init__(self, state: AppState):
        super().__init__()
        self.state = state

        root = QVBoxLayout(self)
        root.addWidget(self._summary_box())

        cl_box = QGroupBox("Local Cl Distribution")
        cl_layout = QVBoxLayout(cl_box)
        self.cl_chart = XYChartWidget(x_label="span", y_label="local Cl")
        cl_layout.addWidget(self.cl_chart)
        root.addWidget(cl_box)

        lift_box = QGroupBox("Lift Distribution vs Ideal Ellipse")
        lift_layout = QVBoxLayout(lift_box)
        self.lift_chart = XYChartWidget(x_label="span", y_label="Cl*chord")
        lift_layout.addWidget(self.lift_chart)
        root.addWidget(lift_box)

        root.addStretch(1)

        state.changed.connect(self.refresh)
        self.refresh()

    def _summary_box(self) -> QGroupBox:
        box = QGroupBox("Cl Distribution Summary")
        form = QFormLayout(box)
        self.lbl_target_cl = add_result_row(form, "Overall CL (target, at stall speed)")
        self.lbl_root_cl = add_result_row(form, "Root Local Cl")
        self.lbl_tip_cl = add_result_row(form, "Tip Local Cl")
        self.lbl_max_cl = add_result_row(form, "Max Local Cl")
        self.lbl_avg_max_ratio = add_result_row(form, "Av/Mx Cl Ratio")
        self.lbl_root_aoa = add_result_row(form, "Solved Root AOA")
        self.lbl_cl_check = add_result_row(form, "Integrated CL Check")
        return box

    def refresh(self) -> None:
        result = self.state.cl_distribution_result()
        cl, *_ = self.state.speed_performance()
        u = self.state.units
        length = units_module.unit_label(u, "length")

        def disp_length(x: float) -> float:
            return units_module.to_display(x, u, "length")

        self.lbl_target_cl.setText(f"{cl:.3f}")
        self.lbl_root_cl.setText(f"{result.root_local_cl:.3f}")
        self.lbl_tip_cl.setText(f"{result.tip_local_cl:.3f}")
        self.lbl_max_cl.setText(
            f"{result.max_local_cl:.3f} at {disp_length(result.max_local_cl_location):.2f} {length}"
        )
        self.lbl_avg_max_ratio.setText(f"{result.avg_over_max_cl_ratio:.3f}")
        self.lbl_root_aoa.setText(f"{result.solved_root_aoa_deg:.2f}°")
        self.lbl_cl_check.setText(f"{result.total_cl_check:.3f}")

        cl_points = [(disp_length(s.span_location), s.local_cl) for s in result.stations]
        self.cl_chart.set_series([ChartSeries("Local Cl", _LOCAL_CL_COLOR, cl_points)])

        lift_points = [(disp_length(s.span_location), disp_length(s.local_lift)) for s in result.stations]
        ellipse_points = [(disp_length(s.span_location), disp_length(s.ellipse_lift)) for s in result.stations]
        self.lift_chart.set_series(
            [
                ChartSeries("Lift Distribution", _LIFT_COLOR, lift_points),
                ChartSeries("Ideal Ellipse", _ELLIPSE_COLOR, ellipse_points, dashed=True),
            ]
        )
