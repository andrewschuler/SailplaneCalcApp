"""First tab: units/tail-type toggles, config save/load, and the static reference content."""
from __future__ import annotations

import json

from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from . import config_io
from .app_state import AppState
from .units import Units

_INSTRUCTIONS_HTML = """
<h3>What does it do?</h3>
<p>Calculates wing and vertical/horizontal tail areas and aspect ratios; tail length and tail
size/span/dihedral design considerations for a polyhedral glider; percent Mean Aerodynamic
Chord and Neutral Point to help determine a center-of-balance location for a first test
flight; converts a conventional tail to a V-tail and vice versa; and estimates stall speed,
lift coefficient, and G-load.</p>
<p>This does not account for airfoils, spanwise flows, wing downwash, or intersection drag,
but is a good starting point for a new model or for checking a manufacturer's numbers.</p>

<h3>Units</h3>
<p>Use the toggle above to switch the whole app between imperial (inches, ounces, mph) and
metric (millimeters, grams, kph) -- every tab's inputs and outputs follow it. Areas display
in in² or dm², and wing loading in oz/ft² or gr/dm², matching each system's usual convention
for a model this size.</p>

<h3>Tail Type</h3>
<p>Pick Cruciform Tail or V-Tail to show only the matching tabs (Quick V-Tail Sizing stays
visible either way, since it converts between the two, and Tail Sizing Checks shows only the
results column for whichever type is selected).</p>

<h3>Configuration</h3>
<p>Save Configuration writes every input on every tab (geometry, gaps, efficiencies, units,
tail type, everything) to a JSON file; Load Configuration reads one back.</p>

<h3>General</h3>
<ul>
<li>Wing tab: up to four sweep panels/breaks. Enter zero span for unused panels. "Effective
Wing Results" projects span/area onto the horizontal plane to account for dihedral -- always
slightly less than the raw "Total Wing Results" for a wing with any dihedral. A Dihedral
Converter tool is included if you'd rather measure an angle than a rise.</li>
<li>Cruciform Tail tab: required for the Cruciform Tail CG, Quick V-Tail Sizing and Tail
Sizing Checks tabs. For a top+bottom vertical (e.g. DLG), use both fin panels.</li>
<li>Cruciform/V-Tail CG tabs: 25-30% MAC (or 5-10% static margin) is a generally accepted
starting point for a safe first test flight. The Neutral Point should never be forward of
the CG. Pick which of static margin / CG distance / %MAC you're specifying with the radio
buttons -- the other two are always derived from it.</li>
<li>Quick V-Tail Sizing: per Mark Drela, these formulas are strictly correct only for large
tail aspect ratios (they ignore local interference/lift cancellation at the V-root during
rudder application), but are much better than guessing.</li>
<li>Speed/Cl/G-Load (Wing tab): pick whether you're specifying a stall speed or a lift
coefficient (Cl); the other, plus the G-load at 4x that stall speed, is derived from it.</li>
</ul>

<h3>Disclaimer</h3>
<p>Data out is only as accurate as data in. This does not account for all the complexities of
flight, but the predictive values work well enough to build and fly a better model airplane.
Further flight testing and trimming is required.</p>
"""

_GLOSSARY_HTML = """
<dl>
<dt><b>Aerodynamic Center (AC)</b></dt><dd>The place where all aerodynamic forces may be
assumed to act as a single force.</dd>
<dt><b>Area</b></dt><dd>Total surface area of a wing, tail, or fin.</dd>
<dt><b>Aspect Ratio (AR)</b></dt><dd>Ratio of the span to the average chord.</dd>
<dt><b>Center of Gravity (CG)</b></dt><dd>The point at which the glider balances fore and
aft.</dd>
<dt><b>Chord</b></dt><dd>A line connecting the leading edge to the trailing edge of a
surface.</dd>
<dt><b>Dihedral</b></dt><dd>The degree of angle (V-shaped bend) viewed from the front or
rear.</dd>
<dt><b>Mean Chord</b></dt><dd>The simple area/span average chord.</dd>
<dt><b>Mean Aerodynamic Chord (MAC)</b></dt><dd>The true aerodynamically-weighted average
chord length, always at least as large as the simple mean chord for a tapered surface.</dd>
<dt><b>Neutral Point (NP)</b></dt><dd>The aerodynamic center of the whole aircraft; the
position through which all net lift acts.</dd>
<dt><b>Polyhedral</b></dt><dd>A wing with more than two panels, where the angle changes at
each joint.</dd>
<dt><b>Reynolds Number</b></dt><dd>A non-dimensional parameter establishing relative viscous
flow effects.</dd>
<dt><b>Span</b></dt><dd>Distance from wingtip to wingtip.</dd>
<dt><b>Static Margin (SM)</b></dt><dd>Distance between the aerodynamic center and the CG, as
a percent of the MAC. A measure of static stability.</dd>
<dt><b>Taper Ratio</b></dt><dd>Tip chord divided by root chord.</dd>
<dt><b>Wing Loading</b></dt><dd>Gross weight each unit of wing area must support in flight.</dd>
</dl>
"""

_CREDITS_HTML = """
<p>Formulas in this app are extracted from two workbooks by Curtis Suter:
<b>SailplaneCalc.xls</b> (April 2005, imperial units) and <b>SailplaneCalcMetric.xlsx</b>
(July 2009, metric units and several additional formulas -- the 4th wing panel, Mean
Aerodynamic Chord length, effective/dihedral-projected wing geometry, taper ratio, sweep
angle, and the Speed/Cl/G-load calculator, all adopted here regardless of which unit system
is selected). Both credit:</p>
<ul>
<li><b>Herk Stokely</b> -- for explaining Mean Aerodynamic Chord, Static Margin, etc.</li>
<li><b>Martin Simons</b> -- <i>Model Aircraft Aerodynamics</i>, source of the wing/tail
geometry and neutral-point formulas.</li>
<li><b>Mark Drela</b> -- source of the Tail Sizing Checks formulas (Radio Controlled Soaring
Digest, Aug 2004).</li>
<li><b>Joe Hahn and Don Stackhouse</b> -- aerodynamic explanations at djaerotech.com.</li>
</ul>
<p>Both original spreadsheets are free to use and redistribute with credit to the author.</p>

<p>The Cl Calcs tab's local Cl / lift-distribution method is ported from <b>LIFTROLL.xlsx</b>,
<b>John Hazel's</b> Lift and Cl calculator for wings (thanks to <b>Bas Breijer</b> for color
formatting and adding individual sweep on 4 panels with 40 vortexes).</p>
"""


class SetupTab(QWidget):
    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        layout = QVBoxLayout(self)

        top_row = QHBoxLayout()

        units_box = QGroupBox("Units")
        units_layout = QVBoxLayout(units_box)
        self.radio_imperial = QRadioButton("Imperial (inches, ounces, mph)")
        self.radio_metric = QRadioButton("Metric (millimeters, grams, kph)")
        group = QButtonGroup(units_box)
        for r in (self.radio_imperial, self.radio_metric):
            group.addButton(r)
            units_layout.addWidget(r)
        (self.radio_imperial if state.units is Units.IMPERIAL else self.radio_metric).setChecked(True)
        self.radio_imperial.toggled.connect(lambda on: on and self._select_units(Units.IMPERIAL))
        self.radio_metric.toggled.connect(lambda on: on and self._select_units(Units.METRIC))
        top_row.addWidget(units_box)

        tail_type_box = QGroupBox("Tail Type")
        tail_type_layout = QVBoxLayout(tail_type_box)
        self.radio_cruciform = QRadioButton("Cruciform Tail (conventional)")
        self.radio_vtail = QRadioButton("V-Tail")
        tail_group = QButtonGroup(tail_type_box)
        for r in (self.radio_cruciform, self.radio_vtail):
            tail_group.addButton(r)
            tail_type_layout.addWidget(r)
        (self.radio_cruciform if state.tail_type == "cruciform" else self.radio_vtail).setChecked(True)
        self.radio_cruciform.toggled.connect(lambda on: on and self._select_tail_type("cruciform"))
        self.radio_vtail.toggled.connect(lambda on: on and self._select_tail_type("vtail"))
        top_row.addWidget(tail_type_box)

        layout.addLayout(top_row)

        config_box = QGroupBox("Configuration")
        config_layout = QHBoxLayout(config_box)
        save_button = QPushButton("Save Configuration...")
        load_button = QPushButton("Load Configuration...")
        save_button.clicked.connect(self._save_configuration)
        load_button.clicked.connect(self._load_configuration)
        config_layout.addWidget(save_button)
        config_layout.addWidget(load_button)
        layout.addWidget(config_box)

        tabs = QTabWidget()
        for title, html in (
            ("Instructions", _INSTRUCTIONS_HTML),
            ("Glossary", _GLOSSARY_HTML),
            ("Credits", _CREDITS_HTML),
        ):
            browser = QTextBrowser()
            browser.setHtml(html)
            tabs.addTab(browser, title)
        layout.addWidget(tabs)

    def _select_units(self, units: Units) -> None:
        self.state.units = units
        self.state.notify()

    def _select_tail_type(self, tail_type: str) -> None:
        self.state.tail_type = tail_type
        self.state.notify()

    def _save_configuration(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", "sailplane_config.json", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            data = config_io.state_to_dict(self.state)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            QMessageBox.warning(self, "Save Failed", f"Could not save configuration:\n{e}")

    def _load_configuration(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load Configuration", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            config_io.apply_dict_to_state(self.state, data)
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as e:
            QMessageBox.warning(self, "Load Failed", f"Could not load configuration:\n{e}")
            return
        self.radio_imperial.setChecked(self.state.units is Units.IMPERIAL)
        self.radio_metric.setChecked(self.state.units is Units.METRIC)
        self.radio_cruciform.setChecked(self.state.tail_type == "cruciform")
        self.radio_vtail.setChecked(self.state.tail_type == "vtail")
        self.state.notify()
