"""Results tab: a single-page, printable summary of every other tab's key numbers -- mirrors
the reference workbook's own "Results" sheet ("Single page printing of results from all of the
above tabs"). Everything here is read from AppState's existing *_result()/*_surface() methods;
no new engine computation happens in this file.
"""
from __future__ import annotations

from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QMessageBox, QPushButton, QTextBrowser, QVBoxLayout, QWidget

from . import units as units_module
from .app_state import AppState
from .units import Units


class ResultsTab(QWidget):
    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        root = QVBoxLayout(self)

        button_row = QHBoxLayout()
        export_button = QPushButton("Export as PDF...")
        export_button.clicked.connect(self._export_pdf)
        button_row.addWidget(export_button)
        button_row.addStretch(1)
        root.addLayout(button_row)

        self.browser = QTextBrowser()
        root.addWidget(self.browser)

        state.changed.connect(self.refresh)
        self.refresh()

    # --- report content ----------------------------------------------------

    def _fmt_len(self, value: float) -> str:
        u = self.state.units
        return f"{units_module.to_display(value, u, 'length'):.2f} {units_module.unit_label(u, 'length')}"

    def _fmt_area(self, value: float) -> str:
        u = self.state.units
        return f"{units_module.to_display(value, u, 'area'):.2f} {units_module.unit_label(u, 'area')}"

    def _fmt_speed(self, value: float) -> str:
        u = self.state.units
        return f"{units_module.to_display(value, u, 'speed'):.2f} {units_module.unit_label(u, 'speed')}"

    @classmethod
    def _section(cls, title: str, rows: list[tuple[str, str]]) -> str:
        row_html = []
        for i, (label, value) in enumerate(rows):
            stripe = ' style="background-color:rgba(0,0,0,0.15);"' if i % 2 == 1 else ""
            row_html.append(
                f"<tr{stripe}>"
                f'<td width="18" style="padding:3px 0;color:#777;">{i + 1}.</td>'
                f'<td width="270" style="padding:3px 10px 3px 0;">{label}</td>'
                f'<td style="padding:3px 0;"><b>{value}</b></td>'
                f"</tr>"
            )
        return (
            f'<table cellspacing="0" cellpadding="0" width="100%" style="margin-top:22px;">'
            f'<tr><td style="background-color:#3a5f7d;color:#ffffff;padding:5px 8px;">'
            f"<b>{title}</b></td></tr></table>"
            f'<table cellspacing="0" cellpadding="0">{"".join(row_html)}</table>'
        )

    def _build_html(self) -> str:
        s = self.state
        u = s.units
        length_label = units_module.unit_label(u, "length")

        wing = s.wing_result()
        surface = wing.surface
        effective = wing.effective

        sections = []

        sections.append(
            self._section(
                "Wing",
                [
                    ("Model Weight", f"{units_module.to_display(s.weight_oz, u, 'weight'):.1f} {units_module.unit_label(u, 'weight')}"),
                    ("Estimated Speed", self._fmt_speed(s.estimated_speed_mph)),
                    ("Total Span", self._fmt_len(surface.total_span)),
                    ("Total Area", self._fmt_area(surface.total_area)),
                    ("Wing Loading", f"{units_module.wing_loading_to_display(s.weight_oz, surface.total_area, u):.2f} {units_module.wing_loading_unit_label(u)}"),
                    ("Mean Chord (area/span)", self._fmt_len(surface.mean_chord)),
                    ("Mean Aerodynamic Chord (length)", self._fmt_len(surface.mac_length)),
                    ("Aspect Ratio", f"{surface.aspect_ratio:.2f}"),
                    ("Taper Ratio", f"{surface.taper_ratio:.2f}"),
                    ("Reynolds Estimate", f"{wing.reynolds_estimate:.0f}"),
                    ("0% MAC Point from Root LE", self._fmt_len(surface.point_0)),
                    ("25% MAC Point from Root LE", self._fmt_len(surface.point_25)),
                    ("Panel Dihedral Angles", ", ".join(f"{d:.1f}°" for d in wing.panel_dihedral_deg)),
                    ("Panel Sweep Angles (LE)", ", ".join(f"{d:.1f}°" for d in surface.panel_sweep_angle_deg)),
                ],
            )
        )

        sections.append(
            self._section(
                "Effective Wing Results (dihedral-projected)",
                [
                    ("Effective Total Span", self._fmt_len(effective.total_span)),
                    ("Effective Total Area", self._fmt_area(effective.total_area)),
                    ("Effective Wing Loading", f"{units_module.wing_loading_to_display(s.weight_oz, effective.total_area, u) if effective.total_area else 0.0:.2f} {units_module.wing_loading_unit_label(u)}"),
                    ("Effective Aspect Ratio", f"{effective.aspect_ratio:.2f}"),
                ],
            )
        )

        cl, stall_speed_mph, max_speed_mph, g_load = s.speed_performance()
        sections.append(
            self._section(
                "Speed / Cl / G-Load",
                [
                    ("Cl", f"{cl:.3f}"),
                    ("Stall Speed", self._fmt_speed(stall_speed_mph)),
                    ("Max Speed", self._fmt_speed(max_speed_mph)),
                    ("G-Load at Max Speed", f"{g_load:.2f} G"),
                ],
            )
        )

        if s.tail_type == "cruciform":
            h = s.horizontal_stab_surface()
            v = s.vertical_fin_surface()
            wing_area = surface.total_area
            sections.append(
                self._section(
                    "Horizontal Stabilizer",
                    [
                        ("Total Span", self._fmt_len(h.total_span)),
                        ("Total Area", self._fmt_area(h.total_area)),
                        ("Mean Aerodynamic Chord", self._fmt_len(h.mac_length)),
                        ("Aspect Ratio", f"{h.aspect_ratio:.2f}"),
                        ("Taper Ratio", f"{h.taper_ratio:.2f}"),
                        ("25% MAC Point from Root LE", self._fmt_len(h.point_25)),
                        ("% of Wing Area", f"{h.total_area / wing_area * 100:.2f} %" if wing_area else "--"),
                    ],
                )
            )
            lower_taper, upper_taper = s.vertical_fin_panel_taper_ratios()
            sections.append(
                self._section(
                    "Vertical Stabilizer (fin)",
                    [
                        ("Total Span", self._fmt_len(v.total_span)),
                        ("Total Area", self._fmt_area(v.total_area)),
                        ("Mean Aerodynamic Chord", self._fmt_len(v.mac_length)),
                        ("Aspect Ratio", f"{v.aspect_ratio:.2f}"),
                        ("Taper Ratio", f"{v.taper_ratio:.2f}"),
                        ("Taper Ratio (bottom panel)", f"{lower_taper:.2f}"),
                        ("Taper Ratio (upper panel)", f"{upper_taper:.2f}"),
                        ("25% MAC Point from Root LE", self._fmt_len(v.point_25)),
                        ("% of Wing Area", f"{v.total_area / wing_area * 100:.2f} %" if wing_area else "--"),
                    ],
                )
            )
            np_result = s.neutral_point_cruciform()
            balance = s.balance_point_cruciform()
            checks = s.tail_checks_cruciform()
        else:
            vtail = s.vtail_geometry()
            equivalent = s.vtail_equivalent_areas()
            sections.append(
                self._section(
                    "V-Tail",
                    [
                        ("Total Span", self._fmt_len(vtail.surface.total_span)),
                        ("Total Area", self._fmt_area(vtail.surface.total_area)),
                        ("Mean Aerodynamic Chord", self._fmt_len(vtail.surface.mac_length)),
                        ("Aspect Ratio", f"{vtail.surface.aspect_ratio:.2f}"),
                        ("Dihedral from Horizontal", f"{vtail.half_dihedral_deg:.1f}°"),
                        ("Included Angle Between V's", f"{vtail.total_angle_deg:.1f}°"),
                        ("Equivalent Horizontal Stab Area", self._fmt_area(equivalent.horizontal_area)),
                        ("Equivalent Vertical Stab Area", self._fmt_area(equivalent.vertical_area)),
                    ],
                )
            )
            np_result = s.neutral_point_vtail()
            balance = s.balance_point_vtail()
            checks = s.tail_checks_vtail()

        sections.append(
            self._section(
                "Balance Point (CG)",
                [
                    ("Neutral Point (% MAC)", f"{np_result.neutral_point_pct_mac:.2f} %"),
                    ("Neutral Point from Root LE", self._fmt_len(np_result.neutral_point_from_root_le)),
                    ("Neutral Point from Root TE", self._fmt_len(np_result.neutral_point_from_root_te)),
                    ("Static Margin (%)", f"{balance.static_margin_pct:.2f} %"),
                    ("CG (% MAC)", f"{balance.cg_pct_mac:.2f} %"),
                    ("CG from Root LE", self._fmt_len(balance.cg_from_root_le)),
                ],
            )
        )

        sections.append(
            self._section(
                "Tail Sizing Checks",
                [
                    ("Equivalent Dihedral Angle (EDA)", f"{checks.eda_deg:.2f}°"),
                    ("Spiral Stability (b)", f"{checks.spiral_stability_b:.2f}"),
                    ("Horizontal Tail Volume (Vh)", f"{checks.tail_volume_h:.3f}"),
                    ("Vertical Tail Volume (Vv)", f"{checks.tail_volume_v:.3f}"),
                    ("Dihedral Sizing - Roll Control (VvB)", f"{checks.roll_control_vvb:.3f}"),
                ],
            )
        )

        tail_type_label = "Cruciform Tail" if s.tail_type == "cruciform" else "V-Tail"
        return (
            "<h1>SailplaneCalc Design Report</h1>"
            f'<p style="color:#888;">Tail configuration: {tail_type_label} &middot; '
            f"Units: {'Imperial' if u is Units.IMPERIAL else 'Metric'}</p>"
            + "".join(sections)
        )

    def refresh(self) -> None:
        self.browser.setHtml(self._build_html())

    # --- export ------------------------------------------------------------

    def _export_pdf(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Report as PDF", "sailplane_report.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        document = QTextDocument()
        document.setHtml(self._build_html())
        try:
            document.print_(printer)
        except OSError as e:
            QMessageBox.warning(self, "Export Failed", f"Could not export PDF:\n{e}")
