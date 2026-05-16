"""Tests for the Python observation_calc.py wrappers (audit T2.1 / D5 / G3).

Live tests gated by `requires_nexus` (need C++ binary built). Verify:
- observe() returns typed ObservableState with all 11 fields populated
- bool wire-format (0/1 numeric) coerces correctly
- kepler_at / composition_rule_evaluate / retarded_time_solve typed wrappers
- shared-bridge mode works for hot-path use
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from astra.physics import (
    NexusBridge,
    ObservableState,
    composition_rule_evaluate,
    kepler_at,
    observe,
    retarded_time_solve,
)

C_LIGHT: float = 299_792_458.0
LIGHT_YEAR: float = 9.4607304725808e15


def _nexus_binary() -> Path:
    here = Path(__file__).resolve()
    return here.parent.parent.parent / "astra_nexus.exe"


pytestmark = pytest.mark.skipif(
    not _nexus_binary().is_file(),
    reason=f"proto/astra_nexus.exe not built at {_nexus_binary()}",
)


# --- observe() end-to-end -------------------------------------------------

@pytest.mark.requires_nexus
def test_observe_rest_one_lightyear_returns_typed_state() -> None:
    state = observe(
        ship_pos=(0.0, 0.0, 0.0),
        ship_velocity=(0.0, 0.0, 0.0),
        t_cosmic=1.0e10,
        body_pos=(0.0, 0.0, -1.0 * LIGHT_YEAR),
        regime="REST",
    )
    assert isinstance(state, ObservableState)
    assert abs(state.d_proper - LIGHT_YEAR) < 1.0
    assert abs(state.v_radial) < 1e-6
    assert abs(state.apparent_rate - 1.0) < 0.02
    assert state.time_reversed is False
    assert state.beyond_photon_history is False
    assert state.beyond_hubble_horizon is False


@pytest.mark.requires_nexus
def test_observe_warp_recede_flags_time_reversed() -> None:
    state = observe(
        ship_pos=(0.0, 0.0, 0.0),
        ship_velocity=(0.0, 0.0, 2.0 * C_LIGHT),
        t_cosmic=1.0e10,
        body_pos=(0.0, 0.0, -1.0 * LIGHT_YEAR),
        regime="WARP_CRUISE",
    )
    assert state.v_radial > 0     # receding
    assert state.apparent_rate < 0
    assert state.time_reversed is True


@pytest.mark.requires_nexus
def test_observe_with_body_t_source_start_flags_photon_history() -> None:
    """Source begins emitting at +1yr; observed from t=0 (1ly lookback ~= -1yr)."""
    one_year = LIGHT_YEAR / C_LIGHT
    state = observe(
        ship_pos=(0.0, 0.0, 0.0),
        ship_velocity=(0.0, 0.0, 0.0),
        t_cosmic=0.0,
        body_pos=(0.0, 0.0, -1.0 * LIGHT_YEAR),
        regime="REST",
        body_t_source_start=one_year,
    )
    assert state.beyond_photon_history is True


@pytest.mark.requires_nexus
def test_observe_far_body_flags_hubble_horizon() -> None:
    state = observe(
        ship_pos=(0.0, 0.0, 0.0),
        ship_velocity=(0.0, 0.0, 0.0),
        t_cosmic=1.0e10,
        body_pos=(0.0, 0.0, -100.0e9 * LIGHT_YEAR),
        regime="REST",
    )
    assert state.beyond_hubble_horizon is True


# --- shared NexusBridge path ----------------------------------------------

@pytest.mark.requires_nexus
def test_observe_shared_bridge_reuses_subprocess() -> None:
    """Passing a long-lived bridge avoids spawning N subprocesses."""
    with NexusBridge() as bridge:
        s1 = observe(
            ship_pos=(0.0, 0.0, 0.0),
            ship_velocity=(0.0, 0.0, 0.0),
            t_cosmic=1.0e10,
            body_pos=(0.0, 0.0, -1.0 * LIGHT_YEAR),
            regime="REST",
            bridge=bridge,
        )
        s2 = observe(
            ship_pos=(0.0, 0.0, 0.0),
            ship_velocity=(0.0, 0.0, 0.0),
            t_cosmic=2.0e10,
            body_pos=(0.0, 0.0, -2.0 * LIGHT_YEAR),
            regime="REST",
            bridge=bridge,
        )
    assert s1.d_proper < s2.d_proper


# --- kepler_at ------------------------------------------------------------

@pytest.mark.requires_nexus
def test_kepler_at_periodicity_via_python_wrapper() -> None:
    a, e, period, t0 = 1.5e11, 0.0167, 3.156e7, 0.0
    phase_t0 = kepler_at(a=a, e=e, period=period, t0=t0, t=0.0)
    phase_p = kepler_at(a=a, e=e, period=period, t0=t0, t=period)
    diff = math.fmod(phase_p - phase_t0 + 4.0 * math.pi, 2.0 * math.pi)
    if diff > math.pi:
        diff -= 2.0 * math.pi
    assert abs(diff) < 1e-6


# --- composition_rule_evaluate --------------------------------------------

@pytest.mark.requires_nexus
def test_composition_rule_evaluate_rest_identity() -> None:
    r = composition_rule_evaluate(
        w_warp=0.0, grav_factor=1.0, gamma_kin=1.0, warp_active=False,
    )
    assert abs(r - 1.0) < 1e-12


@pytest.mark.requires_nexus
def test_composition_rule_evaluate_warp_cruise_half() -> None:
    """W=1.0 with warp_active → f_warp = 0.5; γ=1, grav=1 → 0.5."""
    r = composition_rule_evaluate(
        w_warp=1.0, grav_factor=1.0, gamma_kin=1.0, warp_active=True,
    )
    assert abs(r - 0.5) < 1e-12


# --- retarded_time_solve --------------------------------------------------

@pytest.mark.requires_nexus
def test_retarded_time_solve_one_lightyear() -> None:
    """1 ly lookback ≈ 1 yr; t_cosmic=0 → t_emit ≈ -1 yr."""
    one_year = LIGHT_YEAR / C_LIGHT
    t_emit = retarded_time_solve(
        d_proper=LIGHT_YEAR, z_cosmo=0.0, t_cosmic=0.0,
    )
    assert abs(t_emit + one_year) < one_year * 0.01


# --- ObservableState model shape -----------------------------------------

def test_observable_state_frozen() -> None:
    """ObservableState mirrors the C++ struct shape and is frozen."""
    from pydantic import ValidationError

    state = ObservableState(
        d_proper=1.0e16, v_radial=0.0, z_cosmo=0.001, z_kin=0.0,
        z_metric=0.0, z_total=0.001, t_emit=1.0e10, apparent_rate=1.0,
        time_reversed=False, beyond_photon_history=False,
        beyond_hubble_horizon=False,
    )
    with pytest.raises(ValidationError):
        state.d_proper = 2.0e16


def test_observable_state_negative_d_proper_rejected() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ObservableState(
            d_proper=-1.0, v_radial=0.0, z_cosmo=0.0, z_kin=0.0,
            z_metric=0.0, z_total=0.0, t_emit=0.0, apparent_rate=1.0,
            time_reversed=False, beyond_photon_history=False,
            beyond_hubble_horizon=False,
        )
