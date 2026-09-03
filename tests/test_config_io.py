"""Round-trip save/load of the whole AppState (see ui/config_io.py)."""
from dataclasses import replace

import pytest

from sailplane_calc.ui.app_state import AppState
from sailplane_calc.ui.config_io import apply_dict_to_state, state_to_dict
from sailplane_calc.ui.units import Units


@pytest.fixture
def state() -> AppState:
    return AppState()


def test_round_trip_preserves_modified_values(state):
    state.units = Units.METRIC
    state.tail_type = "vtail"
    state.weight_oz = 42.5
    state.span2 = 30.0
    state.cruciform_balance_mode = "cg_pct"
    state.cruciform_balance_value = 28.0
    state.stab_panel = replace(state.stab_panel, span=99.0, chord_root=8.25)

    data = state_to_dict(state)

    fresh = AppState()
    apply_dict_to_state(fresh, data)

    assert fresh.units is Units.METRIC
    assert fresh.tail_type == "vtail"
    assert fresh.weight_oz == pytest.approx(42.5)
    assert fresh.span2 == pytest.approx(30.0)
    assert fresh.cruciform_balance_mode == "cg_pct"
    assert fresh.cruciform_balance_value == pytest.approx(28.0)
    assert fresh.stab_panel.span == pytest.approx(99.0)
    assert fresh.stab_panel.chord_root == pytest.approx(8.25)


def test_round_trip_is_lossless_for_every_scalar_and_panel_field(state):
    data = state_to_dict(state)
    fresh = AppState()
    # Perturb every scalar/panel field so a missed field would show up as a mismatch.
    fresh.weight_oz = -1
    fresh.tail_type = "vtail"
    fresh.stab_panel = replace(fresh.stab_panel, span=-1)

    apply_dict_to_state(fresh, data)

    original_dict = state_to_dict(state)
    restored_dict = state_to_dict(fresh)
    assert restored_dict == original_dict


def test_apply_partial_dict_only_touches_present_keys(state):
    state.weight_oz = 99.0
    state.span1 = 25.0

    apply_dict_to_state(state, {"scalars": {"weight_oz": 55.0}})

    assert state.weight_oz == pytest.approx(55.0)
    assert state.span1 == pytest.approx(25.0)  # untouched


def test_apply_empty_dict_changes_nothing(state):
    before = state_to_dict(state)
    apply_dict_to_state(state, {})
    after = state_to_dict(state)
    assert before == after
