"""State-coherence migration tests (2026-05-16).

Closes audit D3 (WarpState + cryosleep_active in StateBus), D4
(ReelEntry t_cosmic_at_write required), G4 (WarpState), G5 (callable
detect_regime), G6 (REEL canonical schema), R1 (regime placement
ambiguity resolved in favor of computed-from-truth).

Three concerns are covered here:
1. WarpState validator (W ∈ [0,1], phase Literal, charge_progress ∈ [0,1]).
2. StateBus.regime computed correctly across the canonical state grid;
   incoherent constructions impossible (regime is never settable).
3. ReelEntry requires both clocks (tau_ship and t_cosmic_at_write).

The cross-substrate verification (Python detect_regime matches C++
stdio detect_regime op) lives in tests/test_nexus_bridge.py to keep
the requires_nexus gate consolidated.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from astra.core import Regime, detect_regime
from astra.core.astra_coord import AstraCoord
from astra.core.detect_regime import (
    GRAV_WELL_THRESHOLD,
    STL_REL_BETA_THRESHOLD,
    kinematic_regime_from_rapidity,
)
from astra.core.time_state import TimeState
from astra.harness.reel import ReelEntry
from astra.state_bus import StateBus, WarpState

# --- WarpState validator -------------------------------------------------

def test_warp_state_minimal_valid() -> None:
    w = WarpState(W=0.5, phase="cruising")
    assert w.W == 0.5
    assert w.phase == "cruising"
    assert w.charge_progress == 0.0  # default


def test_warp_state_w_below_zero_rejected() -> None:
    with pytest.raises(ValidationError):
        WarpState(W=-0.1, phase="cruising")


def test_warp_state_w_above_one_rejected() -> None:
    with pytest.raises(ValidationError):
        WarpState(W=1.1, phase="cruising")


def test_warp_state_unknown_phase_rejected() -> None:
    with pytest.raises(ValidationError):
        WarpState(W=0.5, phase="warp_factor_9")  # type: ignore[arg-type]


def test_warp_state_all_phases_accepted() -> None:
    for phase in ("charging", "cruising", "dropping", "shutdown"):
        w = WarpState(W=0.5, phase=phase)  # type: ignore[arg-type]
        assert w.phase == phase


def test_warp_state_charge_progress_bounded() -> None:
    with pytest.raises(ValidationError):
        WarpState(W=0.0, phase="charging", charge_progress=-0.1)
    with pytest.raises(ValidationError):
        WarpState(W=0.0, phase="charging", charge_progress=1.1)


def test_warp_state_frozen() -> None:
    w = WarpState(W=0.5, phase="cruising")
    with pytest.raises(ValidationError):
        w.W = 0.6


# --- StateBus.regime computed ---------------------------------------------

def _bare_state_bus(
    *,
    rapidity_zeta: tuple[float, float, float] = (0.0, 0.0, 0.0),
    warp: WarpState | None = None,
    cryosleep_active: bool = False,
) -> StateBus:
    return StateBus(
        astra_coord=AstraCoord(sx=0, sy=0, sz=0),
        time=TimeState(
            t_cosmic=0.0,
            tau_ship=0.0,
            tau_crew_biological=0.0,
            rapidity_zeta=rapidity_zeta,
        ),
        warp=warp,
        cryosleep_active=cryosleep_active,
    )


def test_state_bus_regime_rest_default() -> None:
    sb = _bare_state_bus()
    assert sb.regime == Regime.REST


def test_state_bus_regime_stl_nonrel_at_low_beta() -> None:
    sb = _bare_state_bus(rapidity_zeta=(0.05, 0.0, 0.0))
    assert sb.regime == Regime.STL_NONREL


def test_state_bus_regime_stl_rel_at_high_beta() -> None:
    sb = _bare_state_bus(rapidity_zeta=(1.0, 0.0, 0.0))
    assert sb.regime == Regime.STL_REL


def test_state_bus_regime_warp_charge_from_warp_phase() -> None:
    sb = _bare_state_bus(warp=WarpState(W=0.0, phase="charging", charge_progress=0.5))
    assert sb.regime == Regime.WARP_CHARGE


def test_state_bus_regime_warp_cruise_from_warp_phase() -> None:
    sb = _bare_state_bus(warp=WarpState(W=1.0, phase="cruising"))
    assert sb.regime == Regime.WARP_CRUISE


def test_state_bus_regime_warp_shutdown_from_dropping_or_shutdown() -> None:
    for phase in ("dropping", "shutdown"):
        sb = _bare_state_bus(warp=WarpState(W=0.5, phase=phase))  # type: ignore[arg-type]
        assert sb.regime == Regime.WARP_SHUTDOWN


def test_state_bus_regime_cryosleep_composes() -> None:
    sb = _bare_state_bus(cryosleep_active=True)
    assert Regime.CRYOSLEEP in sb.regime
    # CRYOSLEEP plus REST base.
    assert (sb.regime & ~Regime.CRYOSLEEP) == Regime.REST


def test_state_bus_regime_cryosleep_plus_warp() -> None:
    sb = _bare_state_bus(
        warp=WarpState(W=1.0, phase="cruising"),
        cryosleep_active=True,
    )
    assert Regime.CRYOSLEEP in sb.regime
    assert Regime.WARP_CRUISE in sb.regime


def test_state_bus_regime_not_in_model_fields() -> None:
    """The schema cannot construct an incoherent state — `regime` lives in
    `model_computed_fields`, not `model_fields`. Attempting to set it via
    the constructor is silently ignored (Pydantic extra=ignore default);
    the source of truth is always the computed derivation.
    """
    assert "regime" not in StateBus.model_fields
    assert "regime" in StateBus.model_computed_fields
    # Sanity: attempting to set regime via kwargs has no effect; the
    # computed value still reflects underlying state.
    sb = StateBus(
        astra_coord=AstraCoord(sx=0, sy=0, sz=0),
        time=TimeState(t_cosmic=0.0, tau_ship=0.0, tau_crew_biological=0.0),
        regime=Regime.WARP_CRUISE,   # type: ignore[call-arg]  # ignored
    )
    assert sb.regime == Regime.REST   # not WARP_CRUISE; the kwarg was dropped


def test_time_state_kinematic_regime_not_in_model_fields() -> None:
    """Same discipline for TimeState.kinematic_regime."""
    assert "kinematic_regime" not in TimeState.model_fields
    assert "kinematic_regime" in TimeState.model_computed_fields


def test_state_bus_regime_warp_overrides_kinematic_base() -> None:
    """When warp is present, base is WARP_*, not the kinematic projection."""
    # Even with high rapidity, warp wins (bubble γ=1; ship is locally inertial).
    sb = _bare_state_bus(
        rapidity_zeta=(1.0, 0.0, 0.0),    # would normally give STL_REL
        warp=WarpState(W=1.0, phase="cruising"),
    )
    assert sb.regime == Regime.WARP_CRUISE
    assert Regime.STL_REL not in sb.regime


# --- detect_regime helper -------------------------------------------------

def test_detect_regime_signature_keyword_only() -> None:
    """Callable surface matches the StateBus.regime computation path."""
    r = detect_regime()
    assert r == Regime.REST


def test_detect_regime_gravity_well_threshold() -> None:
    """grav_factor below threshold composes GRAVITY_WELL bit."""
    r = detect_regime(grav_factor=GRAV_WELL_THRESHOLD - 0.01)
    assert Regime.GRAVITY_WELL in r
    r2 = detect_regime(grav_factor=GRAV_WELL_THRESHOLD + 0.01)
    assert Regime.GRAVITY_WELL not in r2


def test_kinematic_regime_threshold_boundary() -> None:
    """STL_REL_BETA_THRESHOLD is the |β| boundary between STL_NONREL/STL_REL."""
    import math
    # Just below threshold → STL_NONREL
    omega_low = math.atanh(STL_REL_BETA_THRESHOLD - 0.001)
    assert kinematic_regime_from_rapidity((omega_low, 0.0, 0.0)) == Regime.STL_NONREL
    # Just above threshold → STL_REL
    omega_high = math.atanh(STL_REL_BETA_THRESHOLD + 0.001)
    assert kinematic_regime_from_rapidity((omega_high, 0.0, 0.0)) == Regime.STL_REL


# --- ReelEntry dual-clock invariant ---------------------------------------

def test_reel_entry_requires_t_cosmic_at_write() -> None:
    """Spec §4.6 v0.126: t_cosmic_at_write is required for §3.9 dual-clock."""
    with pytest.raises(ValidationError) as exc_info:
        ReelEntry(tau_ship=10.0, body="x")  # type: ignore[call-arg]
    assert "t_cosmic_at_write" in str(exc_info.value)


def test_reel_entry_accepts_both_clocks() -> None:
    e = ReelEntry(tau_ship=10.0, t_cosmic_at_write=1.5e10, body="x")
    assert e.tau_ship == 10.0
    assert e.t_cosmic_at_write == 1.5e10


def test_reel_entry_t_cosmic_at_write_negative_rejected() -> None:
    with pytest.raises(ValidationError):
        ReelEntry(tau_ship=10.0, t_cosmic_at_write=-1.0, body="x")
