from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QScrollArea, QTabWidget, QWidget

from .app_state import AppState
from .cl_calcs_tab import ClCalcsTab
from .cruciform_cg_tab import CruciformCGTab
from .cruciform_tail_tab import CruciformTailTab
from .quick_vtail_tab import QuickVTailTab
from .setup_tab import SetupTab
from .tail_checks_tab import TailChecksTab
from .vtail_cg_tab import VTailCGTab
from .vtail_tab import VTailTab
from .wing_tab import WingTab


def _scrollable(widget: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(widget)
    return scroll


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SailplaneCalc")
        self.resize(1000, 700)

        self.state = AppState()

        self.tabs = QTabWidget()
        self.tabs.addTab(_scrollable(SetupTab(self.state)), "Setup")
        self.tabs.addTab(_scrollable(WingTab(self.state)), "Wing")
        self.tabs.addTab(_scrollable(ClCalcsTab(self.state)), "Cl Calcs")
        self._cruciform_tail_index = self.tabs.addTab(
            _scrollable(CruciformTailTab(self.state)), "Cruciform Tail"
        )
        self._cruciform_cg_index = self.tabs.addTab(
            _scrollable(CruciformCGTab(self.state)), "Cruciform Tail CG"
        )
        self._vtail_index = self.tabs.addTab(_scrollable(VTailTab(self.state)), "V-Tail")
        self._vtail_cg_index = self.tabs.addTab(_scrollable(VTailCGTab(self.state)), "V-Tail CG")
        self.tabs.addTab(_scrollable(QuickVTailTab(self.state)), "Quick V-Tail Sizing")
        self.tabs.addTab(_scrollable(TailChecksTab(self.state)), "Tail Sizing Checks")

        self.setCentralWidget(self.tabs)

        self.state.changed.connect(self._update_tab_visibility)
        self._update_tab_visibility()

    def _update_tab_visibility(self) -> None:
        is_cruciform = self.state.tail_type == "cruciform"
        self.tabs.setTabVisible(self._cruciform_tail_index, is_cruciform)
        self.tabs.setTabVisible(self._cruciform_cg_index, is_cruciform)
        self.tabs.setTabVisible(self._vtail_index, not is_cruciform)
        self.tabs.setTabVisible(self._vtail_cg_index, not is_cruciform)
