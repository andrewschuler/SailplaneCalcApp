"""Shared 'specify balance point by...' control used by both CG tabs.

The workbook lets any of static margin / CG distance / %MAC be hand-typed over a formula
cell, silently orphaning the other two -- this replaces that with an explicit selector so
the other two values are always freshly derived from whichever one the user is editing.
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QButtonGroup, QDoubleSpinBox, QFormLayout, QGroupBox, QRadioButton, QVBoxLayout

from . import units as units_module
from .units import Units
from .widgets import SPIN_BOX_MAX_WIDTH, add_result_row


class BalancePointBox(QGroupBox):
    def __init__(
        self,
        get_mode: Callable[[], str],
        on_mode_change: Callable[[str], None],
        get_value: Callable[[], float],
        set_value: Callable[[float], None],
        get_units: Callable[[], Units],
        notify: Callable[[], None],
    ):
        super().__init__("Balance Point")
        self._get_mode = get_mode
        self._on_mode_change = on_mode_change
        self._get_value = get_value
        self._set_value = set_value
        self._get_units = get_units
        self._notify = notify

        layout = QVBoxLayout(self)

        self.radio_margin = QRadioButton("Static Margin (%)")
        self.radio_pct = QRadioButton("% MAC")
        self.radio_distance = QRadioButton("CG Distance from Root LE")
        group = QButtonGroup(self)
        for r in (self.radio_margin, self.radio_pct, self.radio_distance):
            group.addButton(r)
            layout.addWidget(r)
        {"static_margin": self.radio_margin, "cg_pct": self.radio_pct, "cg_distance": self.radio_distance}[
            get_mode()
        ].setChecked(True)
        self.radio_margin.toggled.connect(lambda on: on and self._select("static_margin"))
        self.radio_pct.toggled.connect(lambda on: on and self._select("cg_pct"))
        self.radio_distance.toggled.connect(lambda on: on and self._select("cg_distance"))

        form = QFormLayout()
        self.spin = QDoubleSpinBox()
        self.spin.setDecimals(2)
        self.spin.setRange(-9999, 9999)
        self.spin.setMaximumWidth(SPIN_BOX_MAX_WIDTH)
        self.spin.valueChanged.connect(self._on_value_changed)
        form.addRow("Value", self.spin)
        layout.addLayout(form)

        results = QFormLayout()
        self.lbl_np_pct = add_result_row(results, "Neutral Point (% MAC)")
        self.lbl_np_le = add_result_row(results, "Neutral Point from Root LE")
        self.lbl_np_te = add_result_row(results, "Neutral Point from Root TE")
        self.lbl_margin = add_result_row(results, "Static Margin (%)")
        self.lbl_pct = add_result_row(results, "CG (% MAC)")
        self.lbl_distance = add_result_row(results, "CG from Root LE")
        layout.addLayout(results)

        self._sync_value_spin()

    def _is_distance_mode(self) -> bool:
        return self._get_mode() == "cg_distance"

    def _sync_value_spin(self) -> None:
        self.spin.blockSignals(True)
        if self._is_distance_mode():
            self.spin.setValue(units_module.to_display(self._get_value(), self._get_units(), "length"))
            self.spin.setSuffix(" " + units_module.unit_label(self._get_units(), "length"))
        else:
            self.spin.setValue(self._get_value())
            self.spin.setSuffix(" %")
        self.spin.blockSignals(False)

    def _select(self, mode: str) -> None:
        if mode != self._get_mode():
            self._on_mode_change(mode)

    def _on_value_changed(self, display_value: float) -> None:
        if self._is_distance_mode():
            canonical = units_module.from_display(display_value, self._get_units(), "length")
        else:
            canonical = display_value
        self._set_value(canonical)
        self._notify()

    def refresh(self, neutral_point, balance_point) -> None:
        self._sync_value_spin()

        u = self._get_units()
        length_label = units_module.unit_label(u, "length")
        np_le = units_module.to_display(neutral_point.neutral_point_from_root_le, u, "length")
        np_te = units_module.to_display(neutral_point.neutral_point_from_root_te, u, "length")
        cg_le = units_module.to_display(balance_point.cg_from_root_le, u, "length")

        self.lbl_np_pct.setText(f"{neutral_point.neutral_point_pct_mac:.2f} %")
        self.lbl_np_le.setText(f"{np_le:.2f} {length_label}")
        self.lbl_np_te.setText(f"{np_te:.2f} {length_label}")
        self.lbl_margin.setText(f"{balance_point.static_margin_pct:.2f} %")
        self.lbl_pct.setText(f"{balance_point.cg_pct_mac:.2f} %")
        self.lbl_distance.setText(f"{cg_le:.2f} {length_label}")

        if neutral_point.neutral_point_from_root_le < balance_point.cg_from_root_le:
            self.lbl_np_le.setText(self.lbl_np_le.text() + " ⚠ NP is forward of CG!")
