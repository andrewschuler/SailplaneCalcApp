"""Small helpers to keep the per-tab UI code declarative and short."""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from PySide6.QtWidgets import QDoubleSpinBox, QFormLayout, QLabel

from . import units as units_module

if TYPE_CHECKING:
    from .app_state import AppState

# A narrow, fixed max width keeps the increment/decrement arrows snug against the value
# instead of stretched across a QFormLayout's full field column (the default field-growth
# behavior) -- applied here so every spin box in the app gets it for free.
SPIN_BOX_MAX_WIDTH = 135


def make_spin(
    value: float,
    on_change: Callable[[float], None],
    *,
    decimals: int = 3,
    step: float = 0.1,
    minimum: float = -9999.0,
    maximum: float = 9999.0,
) -> QDoubleSpinBox:
    """For unit-agnostic fields (angles, ratios, percentages, efficiency, Cl) -- for a
    length/weight/speed field that should respect the imperial/metric toggle, use
    UnitSpinBox instead."""
    spin = QDoubleSpinBox()
    spin.setDecimals(decimals)
    spin.setSingleStep(step)
    spin.setRange(minimum, maximum)
    spin.setValue(value)
    spin.setMaximumWidth(SPIN_BOX_MAX_WIDTH)
    spin.valueChanged.connect(on_change)
    return spin


class UnitSpinBox(QDoubleSpinBox):
    """A spin box that stores/emits a canonical engine-unit value (inches/oz/mph) but
    displays it converted to the app's current unit system, with the right suffix.

    Call `sync()` whenever the canonical value or the unit system may have changed
    externally (every tab's `refresh()`, which already runs on every `state.changed`,
    including unit toggles, is the natural place).
    """

    def __init__(
        self,
        state: "AppState",
        getter: Callable[[], float],
        setter: Callable[[float], None],
        kind: str,
        *,
        decimals: int = 2,
        step: float = 1.0,
        minimum: float = 0.0,
        maximum: float = 999999.0,
    ):
        super().__init__()
        self._state = state
        self._getter = getter
        self._setter = setter
        self._kind = kind
        self.setDecimals(decimals)
        self.setSingleStep(step)
        self.setRange(minimum, maximum)
        self.setMaximumWidth(SPIN_BOX_MAX_WIDTH)
        self.valueChanged.connect(self._on_change)
        self.sync()

    def _on_change(self, display_value: float) -> None:
        canonical = units_module.from_display(display_value, self._state.units, self._kind)
        self._setter(canonical)
        self._state.notify()

    def sync(self) -> None:
        self.blockSignals(True)
        self.setValue(units_module.to_display(self._getter(), self._state.units, self._kind))
        self.setSuffix(" " + units_module.unit_label(self._state.units, self._kind))
        self.blockSignals(False)


def result_label() -> QLabel:
    label = QLabel("--")
    label.setStyleSheet("font-weight: bold;")
    return label


def add_result_row(layout: QFormLayout, caption: str, label: QLabel | None = None) -> QLabel:
    label = label or result_label()
    layout.addRow(caption, label)
    return label
