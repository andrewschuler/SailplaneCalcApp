"""A small generic XY line-chart widget, for curves (unlike PlanformWidget's true-to-shape
outline) where the two axes have unrelated units/magnitudes and should scale independently.

Follows PlanformWidget's set_data()/paintEvent()/_make_transform() pattern: set_series() stores
model-space points and triggers a repaint; paintEvent() builds a plot_rect, computes the
combined x/y extents across all series, and draws gridlines, each series as a polyline, an
optional legend, and axis-extent footer labels.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

_GRID_COLOR = QColor("#3a3a3a")
_ZERO_LINE_COLOR = QColor("#666666")
_LABEL_COLOR = QColor("#aaaaaa")
_GRID_LINE_COUNT = 4


@dataclass
class ChartSeries:
    label: str
    color: QColor
    points: list[tuple[float, float]] = field(default_factory=list)
    dashed: bool = False


class XYChartWidget(QWidget):
    def __init__(self, x_label: str = "", y_label: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self._x_label = x_label
        self._y_label = y_label
        self._series: list[ChartSeries] = []
        self.setMinimumSize(260, 190)

    def set_series(self, series: list[ChartSeries]) -> None:
        self._series = series
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        all_points = [pt for s in self._series for pt in s.points]
        if not all_points:
            painter.setPen(QPen(_LABEL_COLOR))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data")
            return

        margin_left = 44
        margin = 20
        plot_rect = self.rect().adjusted(margin_left, margin - 8, -margin, -margin - 14)

        xs = [x for x, _ in all_points]
        ys = [y for _, y in all_points]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys + [0.0]), max(ys + [0.0])
        x_range = max(x_max - x_min, 1e-9)
        y_range = max(y_max - y_min, 1e-9)

        def to_widget(x: float, y: float) -> QPointF:
            px = plot_rect.left() + (x - x_min) / x_range * plot_rect.width()
            py = plot_rect.bottom() - (y - y_min) / y_range * plot_rect.height()
            return QPointF(px, py)

        self._draw_gridlines(painter, plot_rect, to_widget, y_min, y_max)

        if y_min < 0 < y_max:
            painter.setPen(QPen(_ZERO_LINE_COLOR, 1.0))
            painter.drawLine(to_widget(x_min, 0.0), to_widget(x_max, 0.0))

        for s in self._series:
            if not s.points:
                continue
            pen = QPen(s.color, 1.8)
            if s.dashed:
                pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            path = QPainterPath()
            pts = sorted(s.points, key=lambda p: p[0])
            path.moveTo(to_widget(*pts[0]))
            for pt in pts[1:]:
                path.lineTo(to_widget(*pt))
            painter.drawPath(path)

        if len(self._series) > 1:
            self._draw_legend(painter, plot_rect)

        painter.setPen(QPen(_LABEL_COLOR))
        footer = self.rect().adjusted(4, 0, -4, -4)
        left_text = f"{self._x_label}: {x_min:.1f} .. {x_max:.1f}" if self._x_label else ""
        right_text = f"{self._y_label}: {y_min:.2f} .. {y_max:.2f}" if self._y_label else ""
        painter.drawText(footer, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, left_text)
        painter.drawText(footer, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, right_text)

    def _draw_gridlines(self, painter: QPainter, plot_rect, to_widget, y_min: float, y_max: float) -> None:
        painter.setPen(QPen(_GRID_COLOR, 1.0))
        fm = QFontMetrics(painter.font())
        for i in range(_GRID_LINE_COUNT + 1):
            frac = i / _GRID_LINE_COUNT
            y_value = y_min + frac * (y_max - y_min)
            p = to_widget(0.0, y_value)  # x is irrelevant for a horizontal line's y position
            painter.drawLine(QPointF(plot_rect.left(), p.y()), QPointF(plot_rect.right(), p.y()))
            painter.setPen(QPen(_LABEL_COLOR))
            label = f"{y_value:.2f}"
            painter.drawText(
                QPointF(plot_rect.left() - fm.horizontalAdvance(label) - 6, p.y() + fm.height() / 3),
                label,
            )
            painter.setPen(QPen(_GRID_COLOR, 1.0))

    def _draw_legend(self, painter: QPainter, plot_rect) -> None:
        fm = QFontMetrics(painter.font())
        x = plot_rect.right() - 10
        y = plot_rect.top() + 6
        for s in self._series:
            label_width = fm.horizontalAdvance(s.label)
            swatch_x = x - label_width - 18
            painter.setPen(QPen(s.color, 3))
            painter.drawLine(QPointF(swatch_x, y + fm.height() / 3), QPointF(swatch_x + 12, y + fm.height() / 3))
            painter.setPen(QPen(_LABEL_COLOR))
            painter.drawText(QPointF(swatch_x + 16, y + fm.height() / 1.5), s.label)
            y += fm.height() + 2
