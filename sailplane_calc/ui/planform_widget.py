"""Draws a lifting surface's planform outline with its AC / 25%-MAC marker.

Mirrors the workbook's own chart description: a filled outline (one color per panel, so
sweep/taper breaks are visible at a glance), a dashed "MAC line" at the spanwise MAC
location, and a triangle where that line crosses the 25%-MAC chordwise point. Model-space
(span, chord) coordinates are the engine's canonical inches -- the shape itself is
unit-independent (pure proportions); only the corner extent labels convert for display.
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from . import units as units_module
from .units import Units

_PANEL_COLORS = [QColor("#5a9fd4"), QColor("#4fbf8f"), QColor("#d4a55a"), QColor("#9f7ad4")]
_AC_COLOR = QColor("#e05a5a")
_MAC_LINE_COLOR = QColor("#dddddd")
_LABEL_COLOR = QColor("#aaaaaa")

Point = tuple[float, float]


class PlanformWidget(QWidget):
    def __init__(self, get_units: Callable[[], Units], vertical: bool = False, parent: QWidget | None = None):
        super().__init__(parent)
        self._get_units = get_units
        self._vertical = vertical
        self._panels: list[tuple[int, list[Point]]] = []
        self._point_25 = 0.0
        self._mac_span_location = 0.0
        if vertical:
            self.setMinimumSize(190, 260)
        else:
            self.setMinimumSize(260, 190)

    def set_data(
        self, panels: list[tuple[int, list[Point]]], point_25: float, mac_span_location: float
    ) -> None:
        self._panels = panels
        self._point_25 = point_25
        self._mac_span_location = mac_span_location
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._panels:
            painter.setPen(QPen(_LABEL_COLOR))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No geometry")
            return

        margin = 24
        plot_rect = self.rect().adjusted(margin, margin - 8, -margin, -margin)

        all_points = [pt for _, quad in self._panels for pt in quad]
        spans = [s for s, _ in all_points]
        chords = [c for _, c in all_points]
        span_min, span_max = min(spans), max(spans)
        chord_min = min(chords + [0.0])
        chord_max = max(chords + [self._point_25])
        span_range = max(span_max - span_min, 1e-6)
        chord_range = max(chord_max - chord_min, 1e-6)

        to_widget = self._make_transform(plot_rect, span_min, span_max, span_range, chord_min, chord_range)

        for idx, quad in self._panels:
            color = _PANEL_COLORS[idx % len(_PANEL_COLORS)]
            fill = QColor(color)
            fill.setAlpha(90)
            painter.setPen(QPen(color, 1.5))
            painter.setBrush(QBrush(fill))
            painter.drawPolygon(QPolygonF([to_widget(s, c) for s, c in quad]))

        painter.setPen(QPen(_MAC_LINE_COLOR, 1.2, Qt.PenStyle.DashLine))
        painter.drawLine(
            to_widget(self._mac_span_location, chord_min), to_widget(self._mac_span_location, chord_max)
        )

        self._draw_triangle(painter, to_widget(self._mac_span_location, self._point_25), 6, _AC_COLOR)

        painter.setPen(QPen(_LABEL_COLOR))
        u = self._get_units()
        length_label = units_module.unit_label(u, "length")
        span_text = f"{units_module.to_display(span_range, u, 'length'):.1f} {length_label} span"
        chord_text = f"{units_module.to_display(chord_range, u, 'length'):.1f} {length_label} chord"
        painter.drawText(
            self.rect().adjusted(4, 0, -4, -4),
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
            span_text,
        )
        painter.drawText(
            self.rect().adjusted(4, 0, -4, -4),
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,
            chord_text,
        )

    def _make_transform(self, plot_rect, span_min, span_max, span_range, chord_min, chord_range):
        if self._vertical:
            # Chord fits to width, span fits to height, span increasing UPWARD (a true
            # vertical-tail side view -- Qt's Y grows downward, so larger span = smaller y).
            scale = min(plot_rect.width() / chord_range, plot_rect.height() / span_range)
            pad_x = (plot_rect.width() - chord_range * scale) / 2
            pad_y = (plot_rect.height() - span_range * scale) / 2

            def to_widget(span: float, chord: float) -> QPointF:
                x = plot_rect.left() + pad_x + (chord - chord_min) * scale
                y = plot_rect.top() + pad_y + (span_max - span) * scale
                return QPointF(x, y)

            return to_widget

        scale = min(plot_rect.width() / span_range, plot_rect.height() / chord_range)
        pad_x = (plot_rect.width() - span_range * scale) / 2

        def to_widget(span: float, chord: float) -> QPointF:
            x = plot_rect.left() + pad_x + (span - span_min) * scale
            y = plot_rect.top() + (chord - chord_min) * scale
            return QPointF(x, y)

        return to_widget

    @staticmethod
    def _draw_triangle(painter: QPainter, center: QPointF, size: float, color: QColor) -> None:
        path = QPainterPath()
        path.moveTo(center.x(), center.y() - size)
        path.lineTo(center.x() - size, center.y() + size)
        path.lineTo(center.x() + size, center.y() + size)
        path.closeSubpath()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawPath(path)
