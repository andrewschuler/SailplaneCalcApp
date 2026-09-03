"""Save/load the entire AppState to/from a JSON file."""
from __future__ import annotations

import dataclasses
from typing import Any

from ..engine.models import PanelInput
from .units import Units

_SCALAR_FIELDS = [
    "weight_oz",
    "estimated_speed_mph",
    "chord_root",
    "chord1_tip",
    "chord2_tip",
    "chord3_tip",
    "chord4_tip",
    "span1",
    "span2",
    "span3",
    "span4",
    "sweep1",
    "sweep2",
    "sweep3",
    "sweep4",
    "rise1",
    "rise2",
    "rise3",
    "rise4",
    "twist1_deg",
    "twist2_deg",
    "twist3_deg",
    "twist4_deg",
    "speed_calc_mode",
    "speed_calc_value",
    "gap_wing_te_to_stab_le",
    "gap_wing_te_to_fin_le",
    "cruciform_stab_efficiency",
    "vtail_dihedral_rise",
    "vtail_stab_efficiency",
    "cl_therm",
    "cruciform_balance_mode",
    "cruciform_balance_value",
    "vtail_balance_mode",
    "vtail_balance_value",
    "qv_horizontal_area",
    "qv_vertical_area",
    "qv_v_half_area",
]

_PANEL_FIELDS = ["stab_panel", "fin_lower", "fin_upper", "vtail_panel"]

FORMAT_VERSION = 1


def state_to_dict(state: Any) -> dict:
    data: dict[str, Any] = {
        "version": FORMAT_VERSION,
        "units": state.units.value,
        "tail_type": state.tail_type,
        "scalars": {name: getattr(state, name) for name in _SCALAR_FIELDS},
        "panels": {name: dataclasses.asdict(getattr(state, name)) for name in _PANEL_FIELDS},
    }
    return data


def apply_dict_to_state(state: Any, data: dict) -> None:
    """Tolerant of missing keys (older/partial files) -- only present fields are applied."""
    if "units" in data:
        state.units = Units(data["units"])
    if "tail_type" in data:
        state.tail_type = data["tail_type"]
    for name, value in data.get("scalars", {}).items():
        if name in _SCALAR_FIELDS:
            setattr(state, name, value)
    for name, panel_dict in data.get("panels", {}).items():
        if name in _PANEL_FIELDS:
            setattr(state, name, PanelInput(**panel_dict))
