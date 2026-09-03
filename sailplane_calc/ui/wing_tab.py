from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QButtonGroup,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from ..engine.flight_performance import MAX_SPEED_MULTIPLIER
from ..engine.planform import compute_planform_panels
from . import units as units_module
from .app_state import AppState
from .planform_widget import PlanformWidget
from .widgets import SPIN_BOX_MAX_WIDTH, UnitSpinBox, add_result_row, make_spin
from .xy_chart_widget import ChartSeries, XYChartWidget


class WingTab(QWidget):
    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self._unit_spins: list[UnitSpinBox] = []
        self._angle_spins: list[tuple[str, QDoubleSpinBox]] = []

        root = QVBoxLayout(self)

        general = QGroupBox("Aircraft")
        gform = QFormLayout(general)
        gform.addRow("Model Weight", self._unit_row("weight_oz", "weight", decimals=1))
        gform.addRow("Estimated Speed", self._unit_row("estimated_speed_mph", "speed", decimals=1))
        root.addWidget(general)

        chords = QGroupBox("Chords (breakpoints, root to tip)")
        cform = QFormLayout(chords)
        cform.addRow("Root Chord", self._unit_row("chord_root", "length"))
        cform.addRow("1st Panel Tip Chord", self._unit_row("chord1_tip", "length"))
        cform.addRow("2nd Panel Tip Chord", self._unit_row("chord2_tip", "length"))
        cform.addRow("3rd Panel Tip Chord", self._unit_row("chord3_tip", "length"))
        cform.addRow("4th Panel Tip Chord (0 = no 4th panel)", self._unit_row("chord4_tip", "length"))
        root.addWidget(chords)

        panels_row = QHBoxLayout()
        panels_row.addWidget(self._panel_box("1st Panel", "span1", "sweep1", "rise1", "twist1_deg"))
        panels_row.addWidget(
            self._panel_box("2nd Panel (0 span = unused)", "span2", "sweep2", "rise2", "twist2_deg")
        )
        panels_row.addWidget(
            self._panel_box("3rd Panel (0 span = unused)", "span3", "sweep3", "rise3", "twist3_deg")
        )
        panels_row.addWidget(
            self._panel_box("4th Panel (0 span = unused)", "span4", "sweep4", "rise4", "twist4_deg")
        )
        root.addLayout(panels_row)

        results_row = QHBoxLayout()
        results_row.addWidget(self._total_results_box())
        results_row.addWidget(self._effective_results_box())
        root.addLayout(results_row)

        planform_box = QGroupBox("Planform")
        planform_layout = QVBoxLayout(planform_box)
        self.planform = PlanformWidget(lambda: self.state.units)
        planform_layout.addWidget(self.planform)
        root.addWidget(planform_box)

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self._speed_cl_gload_box())
        bottom_row.addWidget(self._dihedral_helper_box())
        bottom_row.addWidget(self._dihedral_chart_box())
        root.addLayout(bottom_row)
        root.addStretch(1)

        state.changed.connect(self.refresh)
        self.refresh()

    # --- construction helpers --------------------------------------------

    def _unit_row(self, attr: str, kind: str, decimals: int = 2) -> QDoubleSpinBox:
        spin = UnitSpinBox(
            self.state,
            getter=lambda: getattr(self.state, attr),
            setter=lambda v: setattr(self.state, attr, v),
            kind=kind,
            decimals=decimals,
        )
        self._unit_spins.append(spin)
        return spin

    def _panel_box(
        self, title: str, span_attr: str, sweep_attr: str, rise_attr: str, twist_attr: str
    ) -> QGroupBox:
        box = QGroupBox(title)
        form = QFormLayout(box)
        form.addRow("Span", self._unit_row(span_attr, "length"))
        form.addRow("Sweep Offset (from this panel's root)", self._unit_row(sweep_attr, "length"))
        form.addRow("Dihedral Rise (cumulative from wing root)", self._unit_row(rise_attr, "length"))
        form.addRow("Twist at Tip (deg, + = wash-in)", self._angle_row(twist_attr))
        return box

    def _angle_row(self, attr: str) -> QDoubleSpinBox:
        spin = make_spin(
            getattr(self.state, attr),
            lambda v, attr=attr: self._on_angle_change(attr, v),
            decimals=2,
            step=0.1,
            minimum=-45.0,
            maximum=45.0,
        )
        self._angle_spins.append((attr, spin))
        return spin

    def _on_angle_change(self, attr: str, value: float) -> None:
        setattr(self.state, attr, value)
        self.state.notify()

    def _total_results_box(self) -> QGroupBox:
        box = QGroupBox("Total Wing Results")
        rform = QFormLayout(box)
        self.lbl_span = add_result_row(rform, "Total Span")
        self.lbl_area = add_result_row(rform, "Total Area")
        self.lbl_loading = add_result_row(rform, "Wing Loading")
        self.lbl_mac = add_result_row(rform, "Mean Chord (area/span)")
        self.lbl_mac_length = add_result_row(rform, "Mean Aerodynamic Chord (length)")
        self.lbl_ar = add_result_row(rform, "Aspect Ratio")
        self.lbl_taper = add_result_row(rform, "Taper Ratio")
        self.lbl_reynolds = add_result_row(rform, "Reynolds Estimate")
        self.lbl_point0 = add_result_row(rform, "0% MAC Point from Root LE")
        self.lbl_point25 = add_result_row(rform, "25% MAC Point from Root LE")
        self.lbl_dihedral = add_result_row(rform, "Panel Dihedral Angles")
        self.lbl_sweep_angle = add_result_row(rform, "Panel Sweep Angles (LE)")
        return box

    def _effective_results_box(self) -> QGroupBox:
        box = QGroupBox("Effective Wing Results (dihedral-projected)")
        eform = QFormLayout(box)
        self.lbl_eff_span = add_result_row(eform, "Effective Total Span")
        self.lbl_eff_area = add_result_row(eform, "Effective Total Area")
        self.lbl_eff_loading = add_result_row(eform, "Effective Wing Loading")
        self.lbl_eff_ar = add_result_row(eform, "Effective Aspect Ratio")
        return box

    def _dihedral_chart_box(self) -> QGroupBox:
        box = QGroupBox("Does your Dihedral Look like this?")
        layout = QVBoxLayout(box)
        self.dihedral_chart = XYChartWidget(x_label="span", y_label="rise")
        layout.addWidget(self.dihedral_chart)
        return box

    def _dihedral_helper_box(self) -> QGroupBox:
        box = QGroupBox("Dihedral Helper (angle → rise)")
        form = QFormLayout(box)
        self._converter_angle_spins = [
            make_spin(0.0, lambda _v: self._refresh_converter(), decimals=1, step=0.5, minimum=-90, maximum=90)
            for _ in range(4)
        ]
        self._converter_rise_labels = []
        for i, spin in enumerate(self._converter_angle_spins, start=1):
            form.addRow(f"Panel {i} Dihedral Angle (deg)", spin)
            self._converter_rise_labels.append(add_result_row(form, f"Panel {i} Cumulative Rise"))
        return box

    def _speed_cl_gload_box(self) -> QGroupBox:
        box = QGroupBox("Speed / Cl / G-Load")
        layout = QVBoxLayout(box)

        self.radio_stall = QRadioButton("Specify Stall Speed")
        self.radio_cl = QRadioButton("Specify Cl")
        group = QButtonGroup(box)
        for r in (self.radio_stall, self.radio_cl):
            group.addButton(r)
            layout.addWidget(r)
        (self.radio_stall if self.state.speed_calc_mode == "stall_speed" else self.radio_cl).setChecked(True)
        self.radio_stall.toggled.connect(lambda on: on and self._select_speed_mode("stall_speed"))
        self.radio_cl.toggled.connect(lambda on: on and self._select_speed_mode("cl"))

        form = QFormLayout()
        self.speed_value_spin = QDoubleSpinBox()
        self.speed_value_spin.setDecimals(3)
        self.speed_value_spin.setRange(0.01, 9999)
        self.speed_value_spin.setMaximumWidth(SPIN_BOX_MAX_WIDTH)
        self.speed_value_spin.valueChanged.connect(self._on_speed_value_changed)
        form.addRow("Value", self.speed_value_spin)
        layout.addLayout(form)

        results = QFormLayout()
        self.lbl_cl = add_result_row(results, "Cl")
        self.lbl_stall_speed = add_result_row(results, "Stall Speed")
        self.lbl_max_speed = add_result_row(results, f"Max Speed (×{MAX_SPEED_MULTIPLIER:.0f} stall)")
        self.lbl_g_load = add_result_row(results, "G-Load at Max Speed")
        layout.addLayout(results)
        return box

    # --- change handlers ---------------------------------------------------

    def _select_speed_mode(self, mode: str) -> None:
        self.state.speed_calc_mode = mode
        self.state.notify()

    def _on_speed_value_changed(self, display_value: float) -> None:
        if self.state.speed_calc_mode == "stall_speed":
            self.state.speed_calc_value = units_module.from_display(display_value, self.state.units, "speed")
        else:
            self.state.speed_calc_value = display_value
        self.state.notify()

    def _refresh_converter(self) -> None:
        angles = [spin.value() for spin in self._converter_angle_spins]
        rises = self.state.dihedral_converter_rises(angles)
        length_label = units_module.unit_label(self.state.units, "length")
        for label, rise in zip(self._converter_rise_labels, rises):
            display_rise = units_module.to_display(rise, self.state.units, "length")
            label.setText(f"{display_rise:.2f} {length_label}")

    # --- refresh -------------------------------------------------------

    def refresh(self) -> None:
        for spin in self._unit_spins:
            spin.sync()

        for attr, spin in self._angle_spins:
            spin.blockSignals(True)
            spin.setValue(getattr(self.state, attr))
            spin.blockSignals(False)

        u = self.state.units
        length = units_module.unit_label(u, "length")
        area_label = units_module.unit_label(u, "area")

        result = self.state.wing_result()
        s = result.surface

        self.lbl_span.setText(f"{units_module.to_display(s.total_span, u, 'length'):.2f} {length}")
        self.lbl_area.setText(f"{units_module.to_display(s.total_area, u, 'area'):.2f} {area_label}")
        loading = units_module.wing_loading_to_display(self.state.weight_oz, s.total_area, u)
        self.lbl_loading.setText(f"{loading:.2f} {units_module.wing_loading_unit_label(u)}")
        self.lbl_mac.setText(f"{units_module.to_display(s.mean_chord, u, 'length'):.2f} {length}")
        self.lbl_mac_length.setText(f"{units_module.to_display(s.mac_length, u, 'length'):.2f} {length}")
        self.lbl_ar.setText(f"{s.aspect_ratio:.2f}")
        self.lbl_taper.setText(f"{s.taper_ratio:.2f}")
        self.lbl_reynolds.setText(f"{result.reynolds_estimate:.0f}")
        self.lbl_point0.setText(f"{units_module.to_display(s.point_0, u, 'length'):.2f} {length}")
        self.lbl_point25.setText(f"{units_module.to_display(s.point_25, u, 'length'):.2f} {length}")
        self.lbl_dihedral.setText(", ".join(f"{d:.1f}°" for d in result.panel_dihedral_deg))
        self.lbl_sweep_angle.setText(", ".join(f"{d:.1f}°" for d in s.panel_sweep_angle_deg))

        eff = result.effective
        self.lbl_eff_span.setText(f"{units_module.to_display(eff.total_span, u, 'length'):.2f} {length}")
        self.lbl_eff_area.setText(f"{units_module.to_display(eff.total_area, u, 'area'):.2f} {area_label}")
        eff_loading = units_module.wing_loading_to_display(self.state.weight_oz, eff.total_area, u)
        self.lbl_eff_loading.setText(f"{eff_loading:.2f} {units_module.wing_loading_unit_label(u)}")
        self.lbl_eff_ar.setText(f"{eff.aspect_ratio:.2f}")

        panels = compute_planform_panels(self.state.wing_panels(), mirror=True)
        self.planform.set_data(panels, s.point_25, s.mac_span_location)

        dihedral_points = [(0.0, 0.0)]
        cumulative_span = 0.0
        for p in self.state.wing_panels():
            if p.span <= 0:
                continue
            cumulative_span += p.span
            dihedral_points.append((
                units_module.to_display(cumulative_span, u, "length"),
                units_module.to_display(p.dihedral_rise, u, "length"),
            ))
        self.dihedral_chart.set_series([ChartSeries("Dihedral", QColor("#5a9fd4"), dihedral_points)])

        self._refresh_converter()

        self.speed_value_spin.blockSignals(True)
        if self.state.speed_calc_mode == "stall_speed":
            self.speed_value_spin.setValue(
                units_module.to_display(self.state.speed_calc_value, u, "speed")
            )
            self.speed_value_spin.setSuffix(" " + units_module.unit_label(u, "speed"))
        else:
            self.speed_value_spin.setValue(self.state.speed_calc_value)
            self.speed_value_spin.setSuffix("")
        self.speed_value_spin.blockSignals(False)

        cl, stall_speed_mph, max_speed_mph, g_load = self.state.speed_performance()
        speed_label = units_module.unit_label(u, "speed")
        self.lbl_cl.setText(f"{cl:.3f}")
        self.lbl_stall_speed.setText(f"{units_module.to_display(stall_speed_mph, u, 'speed'):.2f} {speed_label}")
        self.lbl_max_speed.setText(f"{units_module.to_display(max_speed_mph, u, 'speed'):.2f} {speed_label}")
        self.lbl_g_load.setText(f"{g_load:.2f} G")
