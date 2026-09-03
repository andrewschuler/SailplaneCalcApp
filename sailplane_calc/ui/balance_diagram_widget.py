"""Draws the wing's MAC as a reference bar with the Neutral Point and CG marked on it --
mirrors the workbook's CG-tab charts ("Blue Dash/Diamond is CG", "Red Triangle/dash is NP",
"Blue Line is the MAC location"), including a red warning tint when NP is forward of CG.
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from . import units as units_module
from .units import Units

_MAC_COLOR = QColor(90, 159, 212, 90)
_ROOT_CHORD_COLOR = QColor("#666666")
_NP_COLOR = QColor("#e05a5a")
_CG_COLOR = QColor("#5a9fd4")
_LABEL_COLOR = QColor("#aaaaaa")
_WARNING_BG = QColor(224, 90, 90, 40)


class BalanceDiagramWidget(QWidget):
    def __init__(self, get_units: Callable[[], Units], parent: QWidget | None = None):
        super().__init__(parent)
        self._get_units = get_units
        self._root_chord = 0.0
        self._point_0 = 0.0
        self._mac_length = 0.0
        self._np_from_root_le = 0.0
        self._cg_from_root_le = 0.0
        self.setMinimumSize(260, 110)

    def set_data(
        self,
        root_chord: float,
        point_0: float,
        mac_length: float,
        np_from_root_le: float,
        cg_from_root_le: float,
    ) -> None:
        self._root_chord = root_chord
        self._point_0 = point_0
        self._mac_length = mac_length
        self._np_from_root_le = np_from_root_le
        self._cg_from_root_le = cg_from_root_le
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        np_forward_of_cg = self._np_from_root_le < self._cg_from_root_le
        if np_forward_of_cg:
            painter.fillRect(self.rect(), _WARNING_BG)

        margin = 30
        baseline_y = self.height() / 2
        left = margin
        right = self.width() - margin

        mac_end = self._point_0 + self._mac_length
        values = [0.0, self._root_chord, self._point_0, mac_end, self._np_from_root_le, self._cg_from_root_le]
        v_min, v_max = min(values), max(values)
        v_range = max(v_max - v_min, 1e-6)
        pad = v_range * 0.08
        v_min -= pad
        v_max += pad
        v_range = v_max - v_min

        def to_x(value: float) -> float:
            return left + (value - v_min) / v_range * (right - left)

        # Root chord reference line
        painter.setPen(QPen(_ROOT_CHORD_COLOR, 2))
        painter.drawLine(QPointF(to_x(0.0), baseline_y), QPointF(to_x(self._root_chord), baseline_y))

        # MAC segment band
        mac_rect = QRectF(to_x(self._point_0), baseline_y - 6, to_x(mac_end) - to_x(self._point_0), 12)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(_MAC_COLOR))
        painter.drawRect(mac_rect)

        # Neutral Point: dashed vertical line + triangle
        np_x = to_x(self._np_from_root_le)
        painter.setPen(QPen(_NP_COLOR, 1.2, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(np_x, baseline_y - 28), QPointF(np_x, baseline_y + 28))
        self._draw_triangle(painter, QPointF(np_x, baseline_y - 28), 6, _NP_COLOR)

        # CG: diamond
        cg_x = to_x(self._cg_from_root_le)
        self._draw_diamond(painter, QPointF(cg_x, baseline_y), 6, _CG_COLOR)

        # Labels
        u = self._get_units()
        length_label = units_module.unit_label(u, "length")
        painter.setPen(QPen(_LABEL_COLOR))
        painter.drawText(
            QRectF(np_x - 60, baseline_y - 44, 120, 14), Qt.AlignmentFlag.AlignCenter, "NP"
        )
        painter.drawText(
            QRectF(cg_x - 60, baseline_y + 12, 120, 14), Qt.AlignmentFlag.AlignCenter, "CG"
        )
        root_text = f"Root Chord: {units_module.to_display(self._root_chord, u, 'length'):.2f} {length_label}"
        painter.drawText(self.rect().adjusted(4, 0, -4, -4), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, root_text)
        if np_forward_of_cg:
            painter.setPen(QPen(_NP_COLOR))
            painter.drawText(
                self.rect().adjusted(4, 0, -4, -4),
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,
                "⚠ NP forward of CG",
            )

    @staticmethod
    def _draw_triangle(painter: QPainter, tip: QPointF, size: float, color: QColor) -> None:
        path = QPainterPath()
        path.moveTo(tip.x(), tip.y())
        path.lineTo(tip.x() - size, tip.y() - size * 1.6)
        path.lineTo(tip.x() + size, tip.y() - size * 1.6)
        path.closeSubpath()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawPath(path)

    @staticmethod
    def _draw_diamond(painter: QPainter, center: QPointF, size: float, color: QColor) -> None:
        path = QPainterPath()
        path.moveTo(center.x(), center.y() - size)
        path.lineTo(center.x() + size, center.y())
        path.lineTo(center.x(), center.y() + size)
        path.lineTo(center.x() - size, center.y())
        path.closeSubpath()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawPath(path)
