"""AppState is the one piece of UI-layer logic worth a direct test: switching which of
static margin / %MAC / CG-distance is used to specify the balance point must preserve the
actual physical balance point, not reinterpret the stale stored number under the new mode's
units (that's exactly the trap the original workbook falls into -- see balance_point_box.py).
"""
import pytest

from sailplane_calc.ui.app_state import AppState


@pytest.fixture
def state() -> AppState:
    return AppState()


@pytest.mark.parametrize("which", ["cruciform", "vtail"])
@pytest.mark.parametrize("new_mode", ["static_margin", "cg_pct", "cg_distance"])
def test_switch_balance_mode_preserves_cg_location(state, which, new_mode):
    get_bp = state.balance_point_cruciform if which == "cruciform" else state.balance_point_vtail
    before = get_bp()

    state.switch_balance_mode(which, new_mode)
    after = get_bp()

    assert after.cg_from_root_le == pytest.approx(before.cg_from_root_le, abs=1e-6)
    assert after.cg_pct_mac == pytest.approx(before.cg_pct_mac, abs=1e-6)
    assert after.static_margin_pct == pytest.approx(before.static_margin_pct, abs=1e-6)


def test_wing_result_reflects_four_panels(state):
    result = state.wing_result()
    assert len(result.surface.panel_areas) == 3  # 4th panel defaults to span=0, unused


def test_cl_distribution_result_matches_speed_performance_cl(state):
    result = state.cl_distribution_result()
    target_cl, *_ = state.speed_performance()
    assert result.stations  # default geometry has active panels
    assert result.total_cl_check == pytest.approx(target_cl, rel=1e-3)


def test_dihedral_converter_matches_stored_rises(state):
    """Round-trips rise -> angle -> rise for the 3 active panels (the default 4th panel has
    span=0, so its angle is defined as 0 and the converter just carries the cumulative rise
    forward rather than reproducing the un-derivable stored rise for an unused panel)."""
    angles = state.wing_result().panel_dihedral_deg
    rises = state.dihedral_converter_rises(angles)
    assert rises[:3] == pytest.approx([state.rise1, state.rise2, state.rise3], abs=0.01)
