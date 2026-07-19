"""Day 1 tests for astra.core + astra.state_bus.

Verifies:
- Pydantic types validate per spec v0.129 §1, §3.3, §3.7, §4.2.
- StateBus and sub-models roundtrip through model_dump → model_validate.
- StateBus is frozen (mutations rejected).
- The watch_47_morning fixture YAML loads into a StateBus.
- Regime bitmask composes (REST | STL_REL | GRAVITY_WELL).
- Rapidity clamp (ω_max ≈ 16.811) rejects oversized rapidity.
- AstraCoord local-offset bound (500 km magnitude) rejects out-of-range.
- CosmologicalParams enforces flat ΛCDM (Ω_m + Ω_Λ = 1).
- BodyState requires exactly one of `position`/`kepler`.

Day 1 scope: schema fit-for-purpose. No physics math, no orchestration.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from astra.core import (
    LOCAL_OFFSET_MAX_M,
    OMEGA_MAX,
    SUBSYSTEMS,
    AstraCoord,
    Regime,
    ShipKinematicState,
    TimeState,
    rapidity_magnitude,
)
from astra.state_bus import (
    BHRecord,
    BodyState,
    ChaosFieldSummary,
    CosmologicalParams,
    KeplerianElements,
    StateBus,
)

# --- AstraCoord ---------------------------------------------------------------

def test_astra_coord_zero_origin_valid() -> None:
    coord = AstraCoord(sx=0, sy=0, sz=0)
    assert coord.lx == 0.0
    assert coord.ly == 0.0
    assert coord.lz == 0.0


def test_astra_coord_at_bound_along_axis_valid() -> None:
    coord = AstraCoord(sx=1, sy=-2, sz=3, lx=LOCAL_OFFSET_MAX_M, ly=0.0, lz=0.0)
    assert coord.lx == LOCAL_OFFSET_MAX_M


def test_astra_coord_axis_over_bound_rejected() -> None:
    with pytest.raises(ValidationError):
        AstraCoord(sx=0, sy=0, sz=0, lx=LOCAL_OFFSET_MAX_M + 1.0)


def test_astra_coord_diagonal_magnitude_over_bound_rejected() -> None:
    # 3 axes at 300 km each: magnitude = √3·300 km ≈ 519.6 km > 500 km
    with pytest.raises(ValidationError):
        AstraCoord(sx=0, sy=0, sz=0, lx=300_000.0, ly=300_000.0, lz=300_000.0)


def test_astra_coord_roundtrip_json() -> None:
    coord = AstraCoord(sx=1, sy=-2, sz=3, lx=100.0, ly=-200.0, lz=300.0)
    coord2 = AstraCoord.model_validate_json(coord.model_dump_json())
    assert coord == coord2


def test_astra_coord_frozen() -> None:
    coord = AstraCoord(sx=0, sy=0, sz=0)
    with pytest.raises(ValidationError):
        coord.sx = 1


# --- Regime -------------------------------------------------------------------

def test_regime_canonical_hex_values() -> None:
    """spec v0.129 §3.3 — values locked as part of save-file wire format."""
    assert Regime.REST.value == 0x00
    assert Regime.STL_NONREL.value == 0x01
    assert Regime.STL_REL.value == 0x02
    assert Regime.WARP_CHARGE.value == 0x04
    assert Regime.WARP_CRUISE.value == 0x08
    assert Regime.WARP_SHUTDOWN.value == 0x10
    assert Regime.GRAVITY_WELL.value == 0x20
    assert Regime.CRYOSLEEP.value == 0x40


def test_regime_gravity_well_composes_with_stl_rel() -> None:
    composed = Regime.STL_REL | Regime.GRAVITY_WELL
    assert composed.value == 0x22
    assert Regime.STL_REL in composed
    assert Regime.GRAVITY_WELL in composed
    assert Regime.WARP_CRUISE not in composed


def test_regime_cryosleep_with_gravity_well() -> None:
    composed = Regime.CRYOSLEEP | Regime.GRAVITY_WELL
    assert composed.value == 0x60
    assert Regime.CRYOSLEEP in composed
    assert Regime.GRAVITY_WELL in composed


# --- Rapidity helpers ---------------------------------------------------------

def test_rapidity_magnitude_pure_math() -> None:
    assert rapidity_magnitude((0.0, 0.0, 0.0)) == 0.0
    assert rapidity_magnitude((3.0, 4.0, 0.0)) == 5.0
    assert rapidity_magnitude((1.0, 2.0, 2.0)) == 3.0


# --- TimeState ----------------------------------------------------------------

def test_time_state_default_kinematic_regime_rest() -> None:
    """TimeState.kinematic_regime is computed (velocity-only projection).
    Zero rapidity → REST. The composite regime lives on StateBus.regime."""
    ts = TimeState(t_cosmic=0.0, tau_ship=0.0, tau_crew_biological=0.0)
    assert ts.kinematic_regime == Regime.REST
    assert ts.rapidity_zeta == (0.0, 0.0, 0.0)
    assert ts.a_proper == (0.0, 0.0, 0.0)


def test_time_state_rapidity_at_clamp_valid() -> None:
    ts = TimeState(
        t_cosmic=1.0,
        tau_ship=1.0,
        tau_crew_biological=1.0,
        rapidity_zeta=(OMEGA_MAX, 0.0, 0.0),
    )
    assert ts.rapidity_zeta[0] == OMEGA_MAX


def test_time_state_rapidity_over_clamp_rejected() -> None:
    with pytest.raises(ValidationError):
        TimeState(
            t_cosmic=1.0,
            tau_ship=1.0,
            tau_crew_biological=1.0,
            rapidity_zeta=(OMEGA_MAX + 0.001, 0.0, 0.0),
        )


def test_kinematic_regime_stl_rel_from_high_rapidity() -> None:
    """High |β| → STL_REL kinematic projection."""
    ts = TimeState(
        t_cosmic=1.0,
        tau_ship=1.0,
        tau_crew_biological=1.0,
        rapidity_zeta=(0.5, 0.0, 0.0),
    )
    assert ts.kinematic_regime == Regime.STL_REL


def test_kinematic_regime_stl_nonrel_from_low_rapidity() -> None:
    """Low |β| (>0 but <0.1) → STL_NONREL kinematic projection."""
    ts = TimeState(
        t_cosmic=1.0,
        tau_ship=1.0,
        tau_crew_biological=1.0,
        rapidity_zeta=(0.01, 0.0, 0.0),
    )
    assert ts.kinematic_regime == Regime.STL_NONREL


def test_time_state_negative_time_rejected() -> None:
    with pytest.raises(ValidationError):
        TimeState(t_cosmic=-1.0, tau_ship=0.0, tau_crew_biological=0.0)


def test_time_state_roundtrip_json() -> None:
    ts = TimeState(
        t_cosmic=1.5e10,
        tau_ship=47.5,
        tau_crew_biological=47.5,
        rapidity_zeta=(0.1, 0.2, 0.3),
        a_proper=(1.0, 0.0, 0.0),
    )
    ts2 = TimeState.model_validate_json(ts.model_dump_json())
    assert ts == ts2


def test_time_state_frozen() -> None:
    ts = TimeState(t_cosmic=0.0, tau_ship=0.0, tau_crew_biological=0.0)
    with pytest.raises(ValidationError):
        ts.tau_ship = 10.0


# --- ShipKinematicState -------------------------------------------------------

def test_ship_kinematic_defaults() -> None:
    # v0.129 §4.2 field set: (v_local_cmb, γ, β, grav_factor, dτ/dt).
    # The v0.128-era `regime` slot is gone (QCR-6): regime lives solely as
    # the StateBus computed field, so a second copy cannot drift.
    sk = ShipKinematicState()
    assert sk.gamma == 1.0
    assert sk.beta == 0.0
    assert sk.grav_factor == 1.0
    assert sk.dilation_ratio == 1.0
    assert not hasattr(sk, "regime")


def test_ship_kinematic_dilation_ratio_bounded() -> None:
    # dτ_ship/dt_cosmic ∈ (0, 1] per spec §4.4 invariants
    with pytest.raises(ValidationError):
        ShipKinematicState(dilation_ratio=0.0)
    with pytest.raises(ValidationError):
        ShipKinematicState(dilation_ratio=1.5)


# --- CosmologicalParams -------------------------------------------------------

def test_cosmo_params_default_flat_lcdm() -> None:
    cp = CosmologicalParams()
    assert cp.c == 299_792_458.0
    assert abs(cp.omega_m + cp.omega_lambda - 1.0) < 1e-9


def test_cosmo_params_non_flat_rejected() -> None:
    with pytest.raises(ValidationError):
        CosmologicalParams(omega_m=0.5, omega_lambda=0.7)


# --- ChaosFieldSummary --------------------------------------------------------

def test_chaos_field_summary_defaults_zero() -> None:
    """v0 placeholder summary; full PDE state lives in proto/astra_nexus (Rig 1)."""
    cfs = ChaosFieldSummary()
    assert cfs.mean_amplitude == 0.0
    assert cfs.max_amplitude == 0.0
    assert cfs.energy_density == 0.0


def test_chaos_field_summary_frozen() -> None:
    cfs = ChaosFieldSummary(mean_amplitude=0.5, max_amplitude=1.0, energy_density=0.25)
    with pytest.raises(ValidationError):
        cfs.mean_amplitude = 0.7


# --- BodyState ----------------------------------------------------------------

def test_body_state_with_position_valid() -> None:
    bs = BodyState(
        name="sun",
        kind="star",
        mass_kg=1.989e30,
        position=(0.0, 0.0, -1.496e11),
    )
    assert bs.position == (0.0, 0.0, -1.496e11)
    assert bs.kepler is None


def test_body_state_with_kepler_valid() -> None:
    kep = KeplerianElements(a=1.496e11, e=0.0167, period_s=3.156e7, parent="sun")
    bs = BodyState(name="earth", kind="planet", mass_kg=5.972e24, kepler=kep)
    assert bs.kepler == kep
    assert bs.position is None


def test_body_state_neither_rejected() -> None:
    with pytest.raises(ValidationError):
        BodyState(name="phantom", kind="planet", mass_kg=1.0)


def test_body_state_both_rejected() -> None:
    kep = KeplerianElements(a=1.0e11, e=0.0, period_s=1.0e7, parent="sun")
    with pytest.raises(ValidationError):
        BodyState(
            name="confused",
            kind="planet",
            mass_kg=1.0,
            position=(0.0, 0.0, 0.0),
            kepler=kep,
        )


def test_keplerian_eccentricity_below_one() -> None:
    # Parabolic/hyperbolic orbits not supported in v0
    with pytest.raises(ValidationError):
        KeplerianElements(a=1.0e11, e=1.0, period_s=1.0e7, parent="sun")


# --- StateBus -----------------------------------------------------------------

def test_state_bus_minimal_construct() -> None:
    sb = StateBus(
        astra_coord=AstraCoord(sx=0, sy=0, sz=0),
        time=TimeState(t_cosmic=0.0, tau_ship=0.0, tau_crew_biological=0.0),
    )
    assert sb.regime == Regime.REST
    assert sb.power_allocation == {}
    assert sb.bh_list == []
    assert sb.cosmo_params.c == 299_792_458.0


def test_state_bus_roundtrip_json() -> None:
    sb = StateBus(
        astra_coord=AstraCoord(sx=0, sy=0, sz=0),
        time=TimeState(t_cosmic=1.0, tau_ship=1.0, tau_crew_biological=1.0),
        bh_list=[
            BHRecord(mass_kg=1.989e30, position=AstraCoord(sx=10, sy=0, sz=0)),
        ],
    )
    sb2 = StateBus.model_validate_json(sb.model_dump_json())
    assert sb == sb2


def test_state_bus_frozen() -> None:
    sb = StateBus(
        astra_coord=AstraCoord(sx=0, sy=0, sz=0),
        time=TimeState(t_cosmic=0.0, tau_ship=0.0, tau_crew_biological=0.0),
    )
    with pytest.raises(ValidationError):
        sb.hull_damage = {"bridge": 0.5}


def test_state_bus_load_watch_47_morning_fixture(textverse_root: str) -> None:
    """Day 1 gate: the watch_47_morning fixture YAML loads into StateBus.

    The fixture mirrors the StateBus schema directly. Day 6 will translate the
    full scenario YAML at astra/scenarios/library/watch_47_morning.yaml; until
    then this fixture demonstrates schema fit-for-purpose.
    """
    fixture_path = (
        Path(textverse_root) / "tests" / "fixtures" / "state_bus_watch_47_morning.yaml"
    )
    raw = yaml.safe_load(fixture_path.read_text(encoding="utf-8"))
    sb = StateBus.model_validate(raw)

    # Initial conditions per scenario watch_47_morning.md
    assert sb.regime == Regime.REST
    assert sb.time.tau_ship == 47.5
    assert sb.time.tau_crew_biological == 47.5
    assert sb.time.rapidity_zeta == (0.0, 0.0, 0.0)
    assert sb.astra_coord.sx == 0
    assert sb.astra_coord.sy == 0
    assert sb.astra_coord.sz == 0

    # Three bodies present per scenario
    assert set(sb.procedural_body_states) == {"sun", "earth", "hot_earth"}
    assert sb.procedural_body_states["sun"].position is not None
    assert sb.procedural_body_states["sun"].kepler is None
    assert sb.procedural_body_states["earth"].kepler is not None
    assert sb.procedural_body_states["earth"].kepler.parent == "sun"
    assert sb.procedural_body_states["hot_earth"].kepler is not None
    assert sb.procedural_body_states["hot_earth"].kepler.period_s == 86400.0

    # Locked subsystem set covered by power allocation
    assert set(sb.power_allocation) == set(SUBSYSTEMS)
    assert abs(sum(sb.power_allocation.values()) - 1.0) < 1e-9

    # Cosmological constants match spec defaults
    assert sb.cosmo_params.c == 299_792_458.0
    assert abs(sb.cosmo_params.omega_m + sb.cosmo_params.omega_lambda - 1.0) < 1e-9


def test_state_bus_roundtrip_fixture(textverse_root: str) -> None:
    """The fixture loads, dumps, and reloads to an equal StateBus."""
    fixture_path = (
        Path(textverse_root) / "tests" / "fixtures" / "state_bus_watch_47_morning.yaml"
    )
    raw = yaml.safe_load(fixture_path.read_text(encoding="utf-8"))
    sb = StateBus.model_validate(raw)
    sb2 = StateBus.model_validate(sb.model_dump(mode="json"))
    assert sb == sb2


# --- Subsystem list -----------------------------------------------------------

def test_subsystems_locked_set() -> None:
    """spec v0.129 §1.4 — locked subsystem list. New entries require amendment."""
    expected = {
        "warp",
        "life_support",
        "hydroponics",
        "sensors",
        "lights",
        "comms",
        "cognitive_cores",
    }
    assert set(SUBSYSTEMS) == expected
