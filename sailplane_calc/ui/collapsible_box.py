"""A generic accordion panel: a checkable header that shows/hides a content widget."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy, QToolButton, QVBoxLayout, QWidget


class CollapsibleBox(QWidget):
    def __init__(self, title: str, collapsed: bool = True, parent: QWidget | None = None):
        super().__init__(parent)

        self.toggle_button = QToolButton()
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(not collapsed)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.ArrowType.DownArrow if not collapsed else Qt.ArrowType.RightArrow)
        self.toggle_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        # `toggled` (not `clicked`) fires for every way the checked state can change --
        # mouse, keyboard activation, and programmatic/accessibility-driven toggles alike.
        self.toggle_button.toggled.connect(self._on_toggled)

        self.content_area = QWidget()
        self.content_area.setVisible(not collapsed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_area)

    def _on_toggled(self, checked: bool) -> None:
        self.content_area.setVisible(checked)
        self.toggle_button.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)

    def set_content_layout(self, layout) -> None:
        # QWidget.setLayout requires no prior layout; content_area is freshly built per use.
        self.content_area.setLayout(layout)
