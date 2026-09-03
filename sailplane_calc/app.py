"""Entry point: `python -m sailplane_calc.app`"""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .ui.app_icon import load_icon
from .ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    icon = load_icon()
    app.setWindowIcon(icon)  # taskbar/dock icon, and the default for any window without its own
    window = MainWindow()
    window.setWindowIcon(icon)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
